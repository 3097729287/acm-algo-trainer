"""Reject placeholder bodies and prefer an existing readable site translation."""
import re


def prose(markdown):
    if not isinstance(markdown, str):
        return ''
    text = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', markdown)
    text = re.sub(r'(?m)^\s*#{1,6}\s+.*$', '', text)
    text = re.sub(r'(?m)^\s*\[[^\]]+\]:\s*\S+.*$', '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'https?://\S+', '', text)
    return re.sub(r'[\s#*_`\[\]()<>:：\-]+', '', text)


def has_body(markdown):
    return any(character.isalpha() for character in prose(markdown))


def japanese_only(markdown):
    text = prose(markdown)
    kana = len(re.findall(r'[\u3040-\u30ff]', text))
    # A Japanese title or quoted word alone is not a language verdict.
    return kana >= 8 and len(re.findall(r'[A-Za-z]', text)) < kana * 3


def markdown_samples(markdown):
    """Recover only explicitly numbered sample input/output fenced pairs."""
    text = str(markdown or '')
    blocks = re.split(r'(?m)(?=^\s*(?:#{1,6}\s*)?样例\s*\$?\d+\$?\s*[:：])', text)
    result = []
    for block in blocks:
        number = re.match(r'^\s*(?:#{1,6}\s*)?样例\s*\$?(\d+)\$?\s*[:：]', block)
        if not number:
            continue
        pair = re.search(r'输入\s*[:：]\s*\n\s*```[^\n]*\n(.*?)\n```\s*\n\s*输出\s*[:：]\s*\n\s*```[^\n]*\n(.*?)\n```', block, re.S)
        if pair:
            result.append({'name': '样例 ' + number[1], 'input': pair[1], 'output': pair[2]})
    return result


def readable_statement(value):
    result = dict(value)
    original = result.get('markdown')
    translation = result.get('translation')
    missing = not has_body(original)
    japanese = (not missing and japanese_only(original)) or (missing and result.get('statementLanguage') == 'ja')
    if (missing or japanese) and isinstance(translation, dict) and translation.get('kind') == 'site':
        translated = translation.get('markdown')
        if has_body(translated) and not japanese_only(translated):
            result.setdefault('sourceMarkdown', original)
            result.update(markdown=translated, statementLanguage='zh', statementSource=translation.get('provider', '原站中文题面'))
            missing = japanese = False
    if missing or japanese:
        result.setdefault('sourceMarkdown', original)
        result.update(markdown=None, statementAvailable=False,
                      statementError='原站仅提供日文题面，暂不收录；需要可用的中文或英文版本。' if japanese else '原站尚未提供完整题目正文，请重试或查看原题。')
        if japanese:
            result['statementLanguage'] = 'ja'
    elif result.get('markdown'):
        result['statementAvailable'] = True
        if not result.get('samples'):
            samples = markdown_samples(result['markdown'])
            if samples:
                result['samples'] = samples
    return result
