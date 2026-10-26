"""Evidence-labelled practice estimates; never manufacture official ratings."""
import math
import re

VERSION = '1.0.17'

OYSTER_URL = 'https://codeforces.com/gym/106695/problem/J'
OYSTER_REVIEW = {
    'difficulty': 1000,
    'difficultySource': 'ToBe 题面与算法复核估算',
    'difficultyEstimated': True, 'difficultyConfidence': 'MEDIUM',
    'difficultyBand': [800, 1200],
    'difficultyEvidence': [OYSTER_URL,
        '每家比较 B 与 12A：整打划算时尽量买整打、余款单买，否则全部单买；线性扫描并保留最小编号，O(N)，64 位整数。',
        '原团队赛通过率不能直接当作个人 CF rating；1000 为 ToBe 复核估计，不是 Codeforces 官方评级。'],
    'metadataVersion': '1.4.4',
}


def normalize_practice_difficulty(row):
    """One hundred-point scale for display, selection and mastery; keep evidence."""
    value = dict(row)
    from urllib.parse import urlsplit
    url = urlsplit(str(value.get('url') or ''))
    if url.hostname in ('codeforces.com', 'www.codeforces.com') and url.path.rstrip('/') == '/gym/106695/problem/J':
        if value.get('difficultyEstimated') is not False or not value.get('difficultySource'):
            value.update(OYSTER_REVIEW)
    rating = value.get('difficulty')
    if isinstance(rating, (int, float)) and not isinstance(rating, bool) and math.isfinite(rating) and rating > 0:
        rounded = int(math.floor(rating / 100 + .5)) * 100
        if rounded != rating:
            value.setdefault('difficultyBeforeRounding', rating)
            value['difficulty'] = rounded
            value['difficultyRounding'] = 'nearest-100-half-up'
    return value

# Reviewed against the public statements: these tasks need a specific algorithm,
# rather than the exponential rating inferred from a small absolute solve count.
WEEKLY_165 = {
    'A': (800, '直接代入计分公式，常数次运算'),
    'B': (800, '线性扫描并统计 (i+p_i) mod k = 0'),
    'C': (1100, '识别需反转的非升前缀，再线性验证整个数组有序'),
    'D': (1700, '按值分组删除位置，用交错前缀和处理剩余段的奇偶翻转'),
    'E': (1900, '合并同色连通块，在缩点树上按中间块和两端颜色统计带权节点对'),
    'F': (2100, '二分步幅，前后缀传播可行区间，枚举峰点检查交集，O(n log V)'),
}


def unknown(source, evidence=None):
    return {'difficulty': None, 'difficultySource': source, 'difficultyEstimated': True,
            'difficultyConfidence': 'UNKNOWN', 'difficultyBand': None,
            'difficultyEvidence': list(evidence or []), 'metadataVersion': VERSION}


def nowcoder(row, statistics=None, max_accepted=None):
    url = row.get('url', '')
    match = re.search(r'/acm/contest/141721/([A-F])$', url)
    if match:
        rating, reason = WEEKLY_165[match[1]]
        return {'difficulty': rating, 'difficultySource': 'ToBe 题面与算法复核估算',
                'difficultyEstimated': True, 'difficultyConfidence': 'MEDIUM',
                'difficultyBand': [max(800, rating - 200), rating + 200],
                'difficultyEvidence': [url, reason, '非牛客官方分数，也非 Codeforces 官方 rating'],
                'metadataVersion': VERSION}
    stats = statistics or {}
    accepted = stats.get('acceptedCount')
    if (not isinstance(accepted, int) or isinstance(accepted, bool) or accepted < 10
            or not isinstance(max_accepted, int) or max_accepted < 100):
        return unknown('牛客未定级 · 缺少足够难度证据', [url, '不按题号、题面对象或零通过数推定高难度'])
    # A compressed within-contest indicator. It is deliberately not presented
    # as a calibrated CF rating. Smoothing avoids extreme values on small tails.
    beginner = bool(re.search(r'周赛|小白月赛', row.get('contest', '')))
    base, slope = (800, 250) if beginner else (1100, 300)
    raw = base + slope * math.log2(max(1, (max_accepted + 20) / (accepted + 20)))
    rating = max(800, min(2800, int(math.floor(raw / 100 + .5)) * 100))
    return {'difficulty': rating, 'difficultySource': 'ToBe 同场统计粗估（非官方）',
            'difficultyEstimated': True, 'difficultyConfidence': 'LOW',
            'difficultyBand': [max(800, rating - 400), rating + 400],
            'difficultyEvidence': [url, f'公开通过人数 {accepted}，同场最高 {max_accepted}',
                                   '平滑并压缩相对通过人数差异；参赛人群不同，不能作为跨平台精确等价分'],
            'metadataVersion': VERSION}
