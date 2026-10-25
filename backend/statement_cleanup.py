"""Remove recognized site notices, never algorithmic background or examples."""
import re


def clean_statement_markdown(value):
    if not isinstance(value, str) or not value:
        return value
    # Match complete prose blocks. Fenced examples/code and all other paragraphs
    # remain byte-for-byte intact, including stories needed to define the task.
    blocks = re.split(r'(\n[ \t]*\n)', value)
    fenced = False
    changed = False
    for index in range(0, len(blocks), 2):
        block = blocks[index]
        if re.search(r'^\s*(`{3,}|~{3,})', block, re.M):
            if len(re.findall(r'^\s*(`{3,}|~{3,})', block, re.M)) % 2:
                fenced = not fenced
            continue
        if fenced:
            continue
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', block)
        text = re.sub(r'<[^>]+>|[*_`]', '', text)
        notice = (re.search(r'学术版|题目总版', text) and re.search(r'受信任|权限等级|发帖.{0,12}权限', text))
        notice = notice or (re.search(r'请勿|请不要|禁止', text) and re.search(r'(?:讨论区|讨论版|题目讨论).{0,16}(?:发|发布|询问|提问).{0,12}(?:题解|代码)', text))
        if notice:
            blocks[index] = ''
            changed = True
    if not changed:
        return value
    result = ''.join(blocks)
    # Drop a now-empty background/notice heading, not a background section.
    result = re.sub(r'^#{1,6}\s*(?:题目背景|Background|公告|站点提示)\s*\n(?:[ \t]*\n)*(?=^#{1,6}\s|\Z)', '', result, flags=re.M|re.I)
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
