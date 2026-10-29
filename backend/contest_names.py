"""Stable display names; problem IDs and original provenance remain unchanged."""
import re
from functools import lru_cache
import json
from problem_titles import problem_title


@lru_cache(maxsize=1)
def event_metadata():
    from paths import resource
    path = resource('contest-event-metadata.json')
    return json.loads(path.read_text('utf8')) if path.exists() else {'names': {}, 'origins': {}}


def natural_key(value):
    return tuple((0, int(p)) if p.isdecimal() else (1, p.casefold()) for p in re.split(r'(\d+)', value))


@lru_cache(maxsize=2048)
def regular_contest(value):
    """Return the registered series/number only when the source says which one.

    A round number is never evidence of its division. This also accepts the
    previous Chinese display names so upgrading does not change task identity.
    """
    name = re.sub(r'\s+', ' ', str(value or '')).strip()
    at = re.fullmatch(r'(?:AtCoder\s+)?(ABC|ARC|AGC|AHC)\s*#?\s*(\d+)', name, re.I)
    if not at:
        at = re.fullmatch(r'AtCoder\s*(初学者赛|常规赛|高难度赛|启发式赛)\s*(\d+)', name)
        if at:
            return dict(初学者赛='ABC', 常规赛='ARC', 高难度赛='AGC', 启发式赛='AHC')[at[1]], int(at[2])
    if at:
        return at[1].upper(), int(at[2])
    if re.search(r'Educational|教育赛', name, re.I):
        match = re.search(r'(?:Round|教育赛(?:第)?)\s*#?\s*(\d+)', name, re.I)
        return ('教育赛', int(match[1])) if match else None
    cf = re.search(r'Codeforces Round\s*#?\s*(\d+).*?Div\.\s*([1-4])(?:\s*\+\s*(?:Div\.\s*)?([1-4]))?', name, re.I)
    if cf:
        return 'Div.' + cf[2] + ('+Div.' + cf[3] if cf[3] else ''), int(cf[1])
    cf = re.fullmatch(r'Div\.\s*([1-4])(?:\s*\+\s*Div\.\s*([1-4]))?\s+#?\s*(\d+)', name, re.I)
    if cf:
        return 'Div.' + cf[1] + ('+Div.' + cf[2] if cf[2] else ''), int(cf[3])
    cf = re.fullmatch(r'Codeforces 第\s*(\d+)\s*轮（第\s*([1-4])(?:、([1-4]))?\s*组）', name)
    if cf:
        return 'Div.' + cf[2] + ('+Div.' + cf[3] if cf[3] else ''), int(cf[1])
    for series in ('小白月赛', '挑战赛', '练习赛', '周赛', '入门赛', '基础赛', '月赛'):
        match = re.search(re.escape(series) + r'(?:\s*Round)?\s*#?\s*(\d+)', name, re.I)
        if match:
            return series, int(match[1])
    lg = re.search(r'LGR\s*-\s*(\d+)', name, re.I)
    return ('月赛', int(lg[1])) if lg else None


def contest_name(value, date=None):
    name = re.sub(r'\s+', ' ', str(value or '')).strip()
    # Shared C++/Python B labels refer to one paper, never a 1 + 7 split.
    name = re.sub(r'(蓝桥杯 20\d{2} C/C\+\+大学B组 初赛)\s*·\s*(?:/Python\s*B\s*)?第二场',r'\1 · 第二场',name)
    regular = regular_contest(name)
    if regular:
        return f'{regular[0]} {regular[1]}'
    alias = event_metadata().get('names', {}).get(name)
    if isinstance(alias, dict) and alias.get('name'):
        return alias['name']
    from contest_translations import xcpc_name
    if re.search(r'[a-zA-Zа-яА-Я]{3}', re.sub(r'ICPC|CCPC|ACM|XCPC', '', name)):
        translated = xcpc_name(name, str(date or '')[:4])
        if translated:
            return translated
    atcoder = re.fullmatch(r'(?:AtCoder\s+)?(ABC|ARC|AGC|AHC)\s*(\d+)', name, re.I)
    if atcoder:
        return f'AtCoder {dict(ABC="初学者赛", ARC="常规赛", AGC="高难度赛", AHC="启发式赛")[atcoder[1].upper()]} {atcoder[2]}'
    camp = re.search(r'(20\d{2})牛客国庆集训派对day\s*(\d+)', name, re.I)
    if camp:
        return f'牛客 {camp[1]} 国庆集训第 {camp[2]} 场'
    # Luogu replays sometimes repeat the English problem-set prefix before
    # the already translated contest name.
    name = re.sub(r'^\[(?:ICPC|CCPC)[^\]]*\]\s*(?=.*[\u4e00-\u9fff])', '', name, flags=re.I)
    name = re.sub(r'^(ICPC|CCPC)\s*(20\d{2})\s*区域赛\s*([\u4e00-\u9fff]+?)站(?:重现赛)?$', r'\1 \2 \3区域赛', name)
    educational = re.search(r'(?:Educational Codeforces Round|教育赛)\s*#?\s*(\d+)', name, re.I)
    if educational:
        return 'Codeforces 教育赛第 ' + educational[1] + ' 轮'
    match = re.search(r'Codeforces Round\s*#?\s*(\d+).*?Div\.\s*([1-4])(?:\s*\+\s*(?:Div\.\s*)?([1-4]))?', name, re.I)
    if match:
        return f'Codeforces 第 {match[1]} 轮（第 {match[2]}' + ('、' + match[3] if match[3] else '') + ' 组）'
    simple = re.fullmatch(r'Div\.([1-4])(?:\+Div\.([1-4]))?\s+(\d+)', name)
    if simple:
        return f'Codeforces 第 {simple[3]} 轮（第 {simple[1]}' + ('、' + simple[2] if simple[2] else '') + ' 组）'
    match = re.search(r'Codeforces Global Round\s*(\d+)', name, re.I)
    if match:
        return 'Codeforces 全球赛第 ' + match[1] + ' 轮'
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
        suffix = '（热身赛）' if re.search(r'热身|Warm.?up', name, re.I) else '（模拟赛）' if '模拟' in name else ''
        series = 'CCPC' if re.search(r'CCPC', name, re.I) else 'ICPC'
        if '青少年' in name:
            return f'{series} {year} 青少年程序设计竞赛{suffix}'.replace('  ', ' ')
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
        cities = dict(zip(
            'Shanghai Nanjing Shenyang Jinan Kunming Macau Macao Beijing Tianjin Hangzhou Qingdao Guilin Wuhan Zhengzhou Jiaozuo Harbin Dalian Changchun Chengdu Chongqing Xuzhou Weihai Nanning Changsha Xiangtan Hefei Xiamen Fuzhou Shenzhen Guangzhou Shijiazhuang Baoding Qinhuangdao Mianyang Nanchang Wuhu Kunshan Suzhou Xiangyang Yinchuan'.split(),
            '上海 南京 沈阳 济南 昆明 澳门 澳门 北京 天津 杭州 青岛 桂林 武汉 郑州 焦作 哈尔滨 大连 长春 成都 重庆 徐州 威海 南宁 长沙 湘潭 合肥 厦门 福州 深圳 广州 石家庄 保定 秦皇岛 绵阳 南昌 芜湖 昆山 苏州 襄阳 银川'.split()))
        city = next((cn for en, cn in cities.items() if cn in name or re.search(en, name, re.I)), None)
        if not city:
            city = next((p for p in ('银川', '杭州', '青岛', '桂林', '西安', '武汉', '郑州', '焦作', '哈尔滨', '大连', '长春', '北京', '天津', '成都', '重庆', '徐州', '威海', '香港', '南宁', '长沙', '湘潭', '合肥', '厦门', '福州', '深圳', '广州', '石家庄', '保定', '秦皇岛', '绵阳', '南昌', '芜湖', '昆山', '苏州', '襄阳') if p in name), None)
        if city:
            kind = '邀请赛' if re.search(r'邀请|Invitational', name, re.I) else '网络赛' if re.search(r'网络|网上|Online', name, re.I) else '区域赛'
            return f'{series} {year} {city}{kind}{suffix}'.replace('  ', ' ')
        if re.search(r'网络|网上|Online', name, re.I):
            locations = ((r'Taiwan|台湾', '台湾'), (r'Japan|日本', '日本'), (r'India|印度', '印度'), (r'Dhaka|达卡', '达卡'))
            area = next((label for pattern,label in locations if re.search(pattern, name, re.I)), None)
            area = area or ('亚洲东区' if re.search(r'Asia.*(?:EC|East)', name, re.I) else '亚洲' if re.search(r'Asia|亚洲', name, re.I) else '')
            round_name = re.search(r'(?:Contest\s*)?\((I{1,3}|[1-3])\)|第([一二三\d]+)场', name, re.I)
            round_name = f'（{round_name[1] or round_name[2]}）' if round_name else ''
            return f'{series} {year} {area}网络赛{round_name}{suffix}'.replace('  ', ' ')
        if re.search(r'ICPC|CCPC', name, re.I) and re.search(r'[A-Za-z]{3}', re.sub(r'ICPC|CCPC', '', name, flags=re.I)):
            rest = re.sub(r'\b(?:The\s+)?(?:19|20)\d{2}(?:\s*[–-]\s*(?:19|20)\d{2})?\b', '', name, count=1, flags=re.I)
            rest = re.sub(r'\b(?:ACM[ -]*)?(?:ICPC|CCPC)\b', '', rest, flags=re.I)
            rest = re.sub(r'^\s*The\s+', '', rest, flags=re.I)
            rest = re.sub(r'\s+', ' ', rest).strip(' ,:-')
            return f'{series} {year} {rest}'.replace('  ', ' ').strip()
    return re.sub(r'Div\.\s*([1-4])', r'Div.\1', name, flags=re.I)


def normalize_row(value):
    value = dict(value)
    original = value.get('contest', '')
    variant = value.get('contestVariant')
    if variant:
        original = re.sub(r'（' + re.escape(variant) + r'）$', '', original)
    value.setdefault('contestFullName', original)
    # Kept first-party provenance wins over an old display label, especially
    # when Div.1 and Div.2 share a round number and some task URLs.
    provenance = value.get('contestFullName', original)
    regular = regular_contest(provenance) or regular_contest(original)
    value['contest'] = f'{regular[0]} {regular[1]}' if regular else contest_name(original, value.get('contestDate') or value.get('startedAt'))
    if regular:
        value.update(series=regular[0], contestFamily=regular[0])
    # Earlier display normalization removed the ICPC/CCPC distinction in
    # provincial events. Recover it from retained first-party provenance.
    full = value.get('contestFullName', '')
    if '省赛' in value['contest'] and re.search(r'ICPC|CCPC', full, re.I):
        value['contest'] = contest_name(full, value.get('contestDate') or value.get('startedAt'))
    if variant:
        value['contest'] += f'（{variant}）'
    origins = event_metadata().get('origins', {})
    event = origins.get(str(value.get('collectionSource', '')).split('?')[0].rstrip('/'))
    if not event:
        event = event_metadata().get('names', {}).get(value['contest'])
    if isinstance(event, dict):
        for key in ('startedAt', 'endedAt', 'contestDate', 'contestDateSource', 'contestDatePrecision', 'eventYear', 'contestDifficulty', 'contestDifficultySource'):
            if key in event:
                value[key] = event[key]
    if value.get('title'):
        value.setdefault('originalTitle', value['title'])
        value['title'] = problem_title(value['title'])
    if re.match(r'^Div\.[1-4](?:\+Div\.[1-4])? \d+$', value['contest']):
        value['series'] = value['contest'].rsplit(' ', 1)[0]
        value['contestFamily'] = value['series']
    elif value['contest'].startswith('教育赛 '):
        value.update(series='教育赛', contestFamily='教育赛')
    return value
