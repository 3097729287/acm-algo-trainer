"""Remove recognized site notices, never algorithmic background or examples."""
import re
from functools import lru_cache
from problem_titles import problem_title

_AD_HEADING = re.compile(r'^(?:广告|广告时间|广告位|推广|商业推广|赞助商推荐|Advertisement|Advertisements|Sponsored)\s*[:：]?$', re.I)
_PROMOTION = re.compile(r'洛谷出品的算法教材|官方(?:网店|店铺).{0,30}(?:热卖|购买|发售)|(?:点击|点此).{0,12}(?:购买|下单)|(?:教材|书籍).{0,20}(?:热卖中|购买链接)', re.I)


def _without_ad_sections(value):
    output, fence, advertising = [], None, None
    for line in value.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif fence == marker[1][0]:
                fence = None
            if advertising is None:
                output.append(line)
            continue
        if fence is not None:
            if advertising is None:
                output.append(line)
            continue
        heading = re.match(r'^(#{1,6})\s+(.+?)\s*#*\s*$', line.strip())
        if advertising is not None and heading and len(heading[1]) <= advertising:
            advertising = None
        if heading and len(heading[1]) >= 2 and _AD_HEADING.fullmatch(heading[2]):
            advertising = len(heading[1])
            continue
        if advertising is None:
            output.append(line)
    return ''.join(output)


def clean_statement_markdown(value):
    if not isinstance(value, str) or not value:
        return value
    # Strings are immutable; identical original/translated statements need not
    # repeat the same prose/fence scan. Large documents bypass the bounded LRU.
    return _cached_markdown(value) if len(value)<=65536 else _clean_markdown(value)


@lru_cache(maxsize=64)
def _cached_markdown(value):
    return _clean_markdown(value)


def _clean_markdown(value):
    original = value
    value = _without_ad_sections(value)
    value = re.sub(r'\A(\ufeff?[ \t]*# )([^\r\n]+)', lambda match: match[1] + problem_title(match[2]), value)
    # Match complete prose blocks. Fenced examples/code and all other paragraphs
    # remain byte-for-byte intact, including stories needed to define the task.
    blocks = re.split(r'(\n[ \t]*\n)', value)
    fenced = False
    changed = value != original
    remove_images = False
    for index in range(0, len(blocks), 2):
        block = blocks[index]
        if re.search(r'^\s*(`{3,}|~{3,})', block, re.M):
            if len(re.findall(r'^\s*(`{3,}|~{3,})', block, re.M)) % 2:
                fenced = not fenced
            continue
        if fenced:
            continue
        if remove_images and re.fullmatch(r'\s*(?:!?\[[^\]]*\]\([^)]*\)|<img\b[^>]*>)\s*', block, re.S | re.I):
            blocks[index] = ''
            changed = True
            continue
        if block.strip():
            remove_images = False
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', block)
        text = re.sub(r'<[^>]+>|[*_`]', '', text)
        notice = (re.search(r'学术版|题目总版', text) and re.search(r'受信任|权限等级|发帖.{0,12}权限', text))
        notice = notice or (re.search(r'请勿|请不要|禁止', text) and re.search(r'(?:讨论区|讨论版|题目讨论).{0,16}(?:发|发布|询问|提问).{0,12}(?:题解|代码)', text))
        promotion = _PROMOTION.search(text)
        notice = notice or promotion
        if notice:
            blocks[index] = ''
            changed = True
            remove_images = bool(promotion)
    if not changed:
        return value
    result = ''.join(blocks)
    # Drop a now-empty background/notice heading, not a background section.
    result = re.sub(r'^(#{1,6})\s*(?:题目背景|Background|公告|站点提示|提示|Hint|Hints|Note|Notes)\s*\n(?:[ \t]*\n)*(?=^#{1,6}\s|\Z)', '', result, flags=re.M|re.I)
    return re.sub(r'\n{3,}', '\n\n', result).strip()


def clean_statement(value):
    if not isinstance(value, dict):
        return value
    result = dict(value)
    result['markdown'] = clean_statement_markdown(value.get('markdown'))
    translation = value.get('translation')
    if isinstance(translation, dict):
        result['translation'] = dict(translation, markdown=clean_statement_markdown(translation.get('markdown')))
        # A bundled translation must retain the original digest if its source
        # was untouched. Cleaned Chinese notices do not change English sources.
    return result
