"""Canonical problem names without leading source/series labels."""
import re

_PREFIX = re.compile(r'^(?:\[([^\]\n]+)\]|【([^】\n]+)】|「([^」\n]+)」|『([^』\n]+)』)[ \t\u3000]*')
_INTERVAL = re.compile(r'[A-Za-z0-9_+*/^\.\s-]+[,，][A-Za-z0-9_+*/^\.\s-]+')


def problem_title(value):
    if not isinstance(value, str):
        return value
    title = value.strip()
    while title.startswith(('[', '【', '「', '『')):
        match = _PREFIX.match(title)
        if not match:
            break
        label = next(part for part in match.groups() if part is not None)
        remaining = title[match.end():].strip()
        if not remaining or _INTERVAL.fullmatch(label):
            break
        title = remaining
    return title


def problem_record(raw, encoded):
    raw, encoded = dict(raw), dict(encoded)
    if isinstance(encoded.get('title'), str):
        before = encoded['title']
        encoded['title'] = problem_title(before)
        if encoded['title'] != before:
            encoded.setdefault('originalTitle', before)
    for key in ('题名', '题目', 'title'):
        if isinstance(raw.get(key), str):
            raw[key] = problem_title(raw[key])
    return raw, encoded
