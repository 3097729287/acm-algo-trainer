"""Statement-subject classification and evidence-based difficulty enrichment.

Original-site tags and ratings take precedence. Statement subjects describe the
problem model, not an unverified solution technique. Estimates use technique
complexity and, when available, relative public acceptance counts in one contest.
"""
import re
from knowledge import enrich_row

SUBJECTS = (
    ('字符串', r'\b(?:string|substring|subsequence|characters?|palindrome|text|letters?|alphabet)\b|字符串|子串|字符|回文|文本'),
    ('图论', r'\b(?:graph|vertices|edges|trees?|nodes?|maze|roads|cities|grid)\b|顶点|节点|结点|边权|无向|有向|迷宫|一棵树|网格|路口|道路'),
    ('计算几何', r'\b(?:polygons?|circles?|rectangles?|triangles?|coordinates?|convex|geometry|dimensional|plane|points?)\b|多边形|圆心|矩形|三角形|坐标|凸包'),
    ('博弈论', r'\b(?:players take turns|play alternately|game theory|nim|winner|loser)\b|轮流|博弈|获胜|胜者|败者'),
    ('位运算', r'\b(?:bitwise|xor|popcount)\b|按位|异或|二进制位'),
    ('期望与概率', r'\b(?:probability|expected value|uniformly at random)\b|概率|期望'),
    ('数学 / 数论', r'\b(?:gcd|lcm|prime|divisors|divisible)\b|公约数|公倍数|质数|素数|整除|约数'),
    ('数学', r'\b(?:integers?|numbers?|sum|product|permutation|sequence|array)\b|整数|数字|数列|数组|序列|排列|求和|乘积'),
    ('数据结构', r'\b(?:queues?|stack|deque|sets?|data structure|automaton)\b|队列|栈|集合|数据结构|自动机'),
    ('交互题', r'\binteractive problem\b|交互题'),
)


def supplement(row, statement='', statistics=None):
    statement = statement or ''
    value = enrich_row(row, statement=statement)
    analysis = value['knowledgeAnalysis']
    # Exclude samples and input/output prose from the model classification.
    description = re.split(r'(?:^|\n)\s*(?:#+\s*)?(?:输入描述|输入格式|Input(?: Format)?|出力|入力|Constraints|样例)\s*(?:\n|:|：)', statement, maxsplit=1, flags=re.I)[0]
    description = re.sub(r'^#.*$', '', description, flags=re.M)
    if not value.get('tags') and not value.get('knowledgeCategories'):
        subjects = [name for name, pattern in SUBJECTS if re.search(pattern, description, re.I)]
        if not subjects and re.search(r'\$[^$]+\$|\\\(|[a-zA-Z]_[a-zA-Z0-9]|\b(?:quantity|count|cost|value|time|size|score|minimum|maximum)\b|数量|计分|得分|计算|时间|总数|重量|速度|价格|人数|大小', description, re.I):
            subjects = ['数学']
        if subjects:
            value['knowledgeCategories'] = subjects[:3]
            analysis.update(categories=subjects[:3], pendingCategories=subjects[:3], source='statement-model', confidence='medium')
            analysis['evidence'].append({'source':'statement-model', 'categories':subjects[:3], 'reason':'题面描述的对象和运算；具体解法尚待题解核验'})
    if value.get('difficulty') is None and statistics:
        from difficulty import nowcoder
        if value.get('platform') == '牛客':
            value.update(nowcoder(value, statistics, statistics.get('maxAccepted')))
    return value
