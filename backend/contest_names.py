"""Stable display names; problem IDs and original provenance remain unchanged."""
import re


def natural_key(value):
    return tuple((0, int(p)) if p.isdecimal() else (1, p.casefold()) for p in re.split(r'(\d+)', value))


def contest_name(value, date=None):
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
    match = re.search(r'(?:牛客)?周赛(?:\s*Round)?\s*(\d+)', name, re.I)
    if match:
        return '周赛 ' + match[1]
    for pattern, series in ((r'(?:牛客)?小白月赛\s*(\d+)', '小白月赛'), (r'(?:牛客)?(?:练习赛|挑战赛)\s*(\d+)', None)):
        match = re.search(pattern, name)
        if match:
            return (series or ('挑战赛' if '挑战赛' in name else '练习赛')) + ' ' + match[1]
    if re.search(r'ICPC|CCPC|大学生程序设计|大学生.*程序设计', name, re.I):
        name = name.replace('澳門', '澳门').replace('熱身賽', '热身赛').replace('正式賽', '正式赛').replace('區域賽', '区域赛')
        year = re.search(r'(?:19|20)\d{2}', name)
        edition = re.search(r'第\s*(\d+)\s*[届屆]', name)
        year = year[0] if year else str(1975 + int(edition[1])) if edition and '区域' in name else str(date or '')[:4]
        year = year if re.fullmatch(r'(?:19|20)\d{2}', year) else ''
        suffix = '（热身赛）' if '热身' in name else ''
        series = 'CCPC' if re.search(r'CCPC', name, re.I) else 'ICPC'
        if re.search(r'EC.?Final|Asia.?East|亚洲东区', name, re.I):
            return f'{series} {year} 亚洲东区决赛{suffix}'.replace('  ', ' ')
        if '小米' in name:
            if '网络' in name:
                round_name = '第一场' if '第一场' in name else '第二场' if '第二场' in name else ''
                return f'{series} {year} 小米网络选拔赛{round_name}{suffix}'.replace('  ', ' ')
            return f'{series} {year} 小米邀请赛决赛{suffix}'.replace('  ', ' ')
        provinces = ('黑龙江', '新疆', '广西', '山东', '四川', '江西', '辽宁', '河南', '陕西', '广东', '浙江', '江苏', '湖北', '湖南', '福建', '安徽', '河北', '吉林', '云南', '贵州', '山西', '海南', '宁夏')
        province = next((p for p in provinces if p in name), None)
        if province and ('省' in name or not re.search(r'区域|邀请', name)):
            if re.search(r'ICPC|CCPC', name, re.I):
                return f'{series} {year} {province}省赛{suffix}'.replace('  ', ' ').strip()
            return f'{province}省赛 {year}{suffix}'.replace('  ', ' ').strip()
        if province and '邀请' in name:
            return f'{series} {year} {province}邀请赛{suffix}'.replace('  ', ' ')
        cities = {'Shanghai':'上海', 'Nanjing':'南京', 'Shenyang':'沈阳', 'Jinan':'济南', 'Kunming':'昆明', 'Macau':'澳门'}
        city = next((cn for en, cn in cities.items() if cn in name or re.search(en, name, re.I)), None)
        if not city:
            city = next((p for p in ('银川', '杭州', '青岛', '桂林', '西安', '武汉', '郑州', '焦作', '哈尔滨', '大连', '长春', '北京', '天津', '成都', '重庆', '徐州', '威海', '香港', '南宁', '长沙', '湘潭', '合肥', '厦门', '福州', '深圳', '广州', '石家庄', '保定', '秦皇岛', '绵阳', '南昌', '芜湖', '昆山', '苏州', '襄阳') if p in name), None)
        if city:
            kind = '邀请赛' if '邀请' in name else '网络赛' if re.search(r'网络|网上|Online', name, re.I) else '区域赛'
            return f'{series} {year} {city}{kind}{suffix}'.replace('  ', ' ')
    return re.sub(r'Div\.\s*([1-4])', r'Div.\1', name, flags=re.I)


def normalize_row(value):
    value = dict(value)
    original = value.get('contest', '')
    value.setdefault('contestFullName', original)
    value['contest'] = contest_name(original, value.get('contestDate') or value.get('startedAt'))
    # Earlier display normalization removed the ICPC/CCPC distinction in
    # provincial events. Recover it from retained first-party provenance.
    full = value.get('contestFullName', '')
    if '省赛' in value['contest'] and re.search(r'ICPC|CCPC', full, re.I):
        value['contest'] = contest_name(full, value.get('contestDate') or value.get('startedAt'))
    if value.get('title'):
        value.setdefault('originalTitle', value['title'])
        value['title'] = re.sub(r'^(?:\[(?:ICPC|CCPC|[A-Z]{2,8}CPC)\s*[^\]]+\]\s*)+', '', value['title'], flags=re.I)
    if re.match(r'^Div\.[1-4](?:\+Div\.[1-4])? \d+$', value['contest']):
        value['series'] = value['contest'].rsplit(' ', 1)[0]
        value['contestFamily'] = value['series']
    elif value['contest'].startswith('教育赛 '):
        value.update(series='教育赛', contestFamily='教育赛')
    return value
