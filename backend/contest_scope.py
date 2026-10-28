"""Requested public catalogue scope; private records remain addressable by ID.

Recognise event provenance, including labelled Luogu mirrors. English problem
titles, ordinary CF rounds and AtCoder contests are not geographic evidence.
"""
import re
import json
from functools import lru_cache

VERSION = 'china-xcpc-20261028-v3'
_XCPC = re.compile(r'\b(?:ICPC|CCPC|XCPC|ACM|N[WE]ERC|S[WE]ERC|SEERC|NCPC|GCPC|NAC|ECNA|CERC|NEERC)\b|Collegiate Programming|大学生.*程序设计', re.I)
_WORLD = re.compile(r'World\s*Finals?|全球总决赛|\bWF\b', re.I)
_FINALS = re.compile(r'决赛|\bFinals?\b', re.I)
_ONLINE = re.compile(r'网络(?:预选|资格|选拔)?赛|\bOnline\b', re.I)
_FOREIGN = re.compile(
    r'东南欧|西南欧|西北欧|中欧|北欧|北美|南美|拉丁美洲|东西伯利亚|俄罗斯|乌拉尔|莫斯科|'
    r'德国|瑞士|希腊|哥伦比亚|墨西哥|巴西|玻利维亚|吉尔吉斯斯坦|叙利亚|'
    r'日本|横滨|筑波|东京|韩国|大田|首尔|雅加达|马尼拉|曼谷|佛统|达卡|德黑兰|'
    r'印度|阿姆里塔普里|坎普尔|克勒格布尔|瓜廖尔|金奈|哥印拜陀|喀布尔|河内|岘港|胡志明|泰国|马来西亚|'
    r'\b(?:NAC|NWERC|SWERC|SEERC|NCPC|GCPC|ECNA|CERC|NEERC|NERC)\b|'
    r'\b(?:Europe(?:an)?|Eurasia|America(?:n)?|Nordic|German|Swiss|Greek|Greece|Russia(?:n)?|Siberia(?:n)?|Moscow|Ural|'
    r'Colombia|Columbia University|Mexico|Brazil(?:ian)?|UFBA|Bolivia|Kyrgyzstan|Syri(?:a|an)|HIAST|Samara|'
    r'Japan|Yokohama|Tsukuba|Tokyo|Taejon|Daejeon|Seoul|Korea|Jakarta|Manila|Bangkok|Nakhon Pathom|Dhaka|Tehran|'
    r'India|Amritapuri|Kanpur|Kharagpur|Gwalior|Chennai|Coimbatore|Kabul|Hanoi|Danang|Ho Chi Minh|Thailand|Malaysia)\b|'
    r'Самар[а-яё]*|Всероссийск[а-яё]*', re.I)


@lru_cache(maxsize=1)
def removals():
    from paths import resource
    path = resource('excluded-xcpc.json')
    rows = json.loads(path.read_text('utf8'))['problems'] if path.is_file() else []
    return {row['id'] for row in rows}, {row['url'].split('?')[0].split('#')[0] for row in rows if row.get('url')}


def excluded(row):
    row = row.get('encoded', row)
    ids, urls = removals()
    if row.get('id') in ids or str(row.get('url') or '').split('?')[0].split('#')[0] in urls:
        return True
    # Restrict matching to event/source labels, never the statement or tags.
    events = [str(row.get(k) or '') for k in ('contest', 'contestFullName', 'xcpcPlace')]
    events += [str(row.get('场次') or '')]
    title = str(row.get('originalTitle') or row.get('题名') or '')
    # Mirror prefixes may be preceded by another source label, e.g. HNOI/WF.
    events += re.findall(r'\[([^\]\n]+)\]|【([^】\n]+)】', title)
    text = ' '.join(' '.join(value) if isinstance(value, tuple) else value for value in events)
    return bool(_XCPC.search(text) and (_WORLD.search(text) or _FOREIGN.search(text)
                                      or _FINALS.search(text) or _ONLINE.search(text)))
