"""Stable display names; problem IDs and original provenance remain unchanged."""
import re


def natural_key(value):
    return tuple((0, int(p)) if p.isdecimal() else (1, p.casefold()) for p in re.split(r'(\d+)', value))


def contest_name(value):
    name = re.sub(r'\s+', ' ', str(value or '')).strip()
    # Luogu replays sometimes repeat the English problem-set prefix before
    # the already translated contest name.
    name = re.sub(r'^\[(?:ICPC|CCPC)[^\]]*\]\s*(?=.*[\u4e00-\u9fff])', '', name, flags=re.I)
    name = re.sub(r'^(ICPC|CCPC)\s*(20\d{2})\s*区域赛\s*([\u4e00-\u9fff]+?)站(?:重现赛)?$', r'\1 \2 \3区域赛', name)
    educational = re.search(r'(?:Educational Codeforces Round|教育赛)\s*#?\s*(\d+)', name, re.I)
    if educational:
        return '教育赛 ' + educational[1]
    match = re.search(r'Codeforces Round\s*#?\s*(\d+).*?Div\.\s*([1-4])(?:\s*\+\s*(?:Div\.\s*)?([1-4]))?', name, re.I)
    if match:
        return 'Div.' + match[2] + ('+Div.' + match[3] if match[3] else '') + ' ' + match[1]
    match = re.search(r'Codeforces Global Round\s*(\d+)', name, re.I)
    if match:
        return 'Global ' + match[1]
    return re.sub(r'Div\.\s*([1-4])', r'Div.\1', name, flags=re.I)


def normalize_row(value):
    value = dict(value)
    original = value.get('contest', '')
    value.setdefault('contestFullName', original)
    value['contest'] = contest_name(original)
    if re.match(r'^Div\.[1-4](?:\+Div\.[1-4])? \d+$', value['contest']):
        value['series'] = value['contest'].rsplit(' ', 1)[0]
        value['contestFamily'] = value['series']
    elif value['contest'].startswith('教育赛 '):
        value.update(series='教育赛', contestFamily='教育赛')
    return value
