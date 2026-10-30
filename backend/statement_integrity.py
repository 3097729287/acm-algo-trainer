"""Statement evidence and task capabilities; completeness is not sample count."""
import re
from urllib.parse import urlsplit


def native_submission_supported(url):
    """Catalogue capability of the existing native adapters, without a POST."""
    try:
        p = urlsplit(url or '')
        if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443) or p.query:
            return False
        patterns = {
            'codeforces.com': r'/(?:contest|gym)/\d+/problem/[A-Za-z]\d?|/problemset/problem/\d+/[A-Za-z]\d?',
            'www.codeforces.com': r'/(?:contest|gym)/\d+/problem/[A-Za-z]\d?|/problemset/problem/\d+/[A-Za-z]\d?',
            'atcoder.jp': r'/contests/[\w-]+/tasks/[\w-]+',
            'ac.nowcoder.com': r'/acm/(?:contest/\d+/[A-Za-z]\d?|problem/[1-9]\d{0,19})',
            'www.luogu.com.cn': r'/problem/[A-Za-z0-9_]+',
            'luogu.com.cn': r'/problem/[A-Za-z0-9_]+',
            'qoj.ac': r'/problem/[1-9]\d*',
        }
        pattern = patterns.get((p.hostname or '').lower())
        return bool(pattern and re.fullmatch(pattern, p.path))
    except (TypeError, ValueError):
        return False

SPECIAL_TYPES = {'interactive', 'communication', 'output-only', 'attachment'}


def statement_type(value):
    explicit = value.get('problemType') or value.get('taskType')
    if explicit in SPECIAL_TYPES:
        return explicit
    if value.get('communication') is True:
        return 'communication'
    if value.get('interactive') is True:
        return 'interactive'
    body = value.get('sourceText') or value.get('markdown') or ''
    # Only affirmative task declarations, never a title or an incidental word.
    text = re.sub(r'[*_]', '', body)
    if re.search(r'(?m)^#{2,6}\s*(?:Communication|通信)\s*$',text):
        return 'communication'
    if re.search(r'(?m)^#{2,6}\s*(?:Interaction|交互(?:方式|协议|过程)?)\s*$',text):
        return 'interactive'
    if re.search(r'\bthis is (?:an? |the )?(?:two[- ]steps? |multi[- ]steps? )?communication (?:problem|task)\b|本题(?:是一道|是一个|为|是)通信|这是一道通信题', text, re.I):
        return 'communication'
    if re.search(r'\bthis (?:is an?|problem is|task is) interactive(?: (?:problem|task))?\b|这是(?:一道|一个)?交互(?:式)?(?:题|问题)|本题(?:是一道|是一个|为|是)交互|本题为交互式任务', text, re.I):
        return 'interactive'
    if re.search(r'\bthis is an? output[- ]only (?:problem|task)\b|这是一道(?:提交答案|答案提交)题|本题(?:是一道|为|是)(?:提交答案|答案提交)题|题目类型[：:]\s*提交答案|这是一道结果填空的题|结果填空题', text, re.I):
        return 'output-only'
    return 'standard'


def ordinary_samples(value):
    return (statement_type(value) == 'standard'
            and value.get('localJudgeSupported') is not False
            and (value.get('integrity') or {}).get('status') not in ('incomplete', 'unresolved'))


def valid_samples(value):
    samples = value.get('samples')
    return isinstance(samples, list) and all(isinstance(s, dict)
        and isinstance(s.get('input'), str) and isinstance(s.get('output'), str) for s in samples)


def content_complete(value):
    if not isinstance(value, dict) or not value.get('markdown'):
        return False
    from statement_quality import has_body
    if not has_body(value['markdown']) or not valid_samples(value):
        return False
    evidence = value.get('integrity') or {}
    if evidence.get('status') in ('incomplete', 'unresolved'):
        return False
    # The source can legitimately supply no examples, especially for special
    # tasks. New zero-example statements require an explicit source inventory.
    return bool(value['samples'] or evidence.get('sourceVerified') is True
                and (evidence.get('sampleCount') == 0 or evidence.get('pdfPageCountVerified') is True))


def annotate_type(value):
    result = dict(value)
    kind = statement_type(result)
    result['problemType'] = kind
    result['localJudgeSupported'] = kind == 'standard' and result.get('localJudgeSupported') is not False
    return result


def finalize_source(value, client):
    """Save resource failure as evidence, never as a complete offline statement."""
    import datetime
    from statement_resources import archive_resources
    result = archive_resources(annotate_type(value), client)
    from statement_quality import has_body
    pdf = result.get('statementPdf')
    pdf_verified = bool(isinstance(pdf, dict) and pdf.get('data') and pdf.get('pageCount'))
    if pdf_verified and not result.get('samples'):
        result['localJudgeSupported'] = False
    result['integrity'] = {'schema': 1, 'sourceVerified': True,
        'status': 'incomplete' if result['resourceIssues'] or not has_body(result.get('markdown')) or not valid_samples(result) else 'complete',
        'sampleCount': len(result.get('samples') or []), 'pdfPageCountVerified': pdf_verified,
        'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    return result
