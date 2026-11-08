"""Explicit above-cutoff reviews after reading the full suffix/palindrome lists."""
from nowcoder_editorials import problem, review_rating, sha, statement


def run():
    pairs = {
        237303: ('luogu-training-P3809', '牛客多组总长百万，要求后缀数组并附相邻LCP；在原SA模板基础上增加线性height计算，沿用2400档。'),
        20422: ('luogu-training-P4287', '已查看牛客原题图片，双倍回文准确形式为w wR w wR，总长度必须为四倍数；最大长度五十万、样例与原题一致。'),
        236737: ('luogu-training-P3649', '同样求回文子串的长度乘出现次数最大值，n<=三十万；需回文树状态、失败链接计数传播与64位贡献。'),
    }
    for number, (source_id, reason) in pairs.items():
        source = problem(source_id)
        review_rating(number, source['difficulty'], reason + ' 使用ToBe已有CF-EQ映射档，非牛客官方数值评级。',
                      origin={'id': source_id, 'url': source['url'], 'difficultySource': source.get('difficultySource'),
                              'sourceStatementSha256': sha(statement(source_id)['markdown'])})
    reviews = {
        17141: (2600, ['后缀数组', '字符串同构'], '三字符字母表，n<=五万、多组总长二十万，求按单射重命名视为同构的子串类别数；普通不同子串计数不适用。需规范同构表示，或对六种字母置换建立后缀结构、计算并集并修正只使用一种字符的轨道大小。'),
        233969: (2500, ['AC自动机', '树上字符串'], '百万结点母系树、百万总查询长度，姓名按新字符前置且全名不能显式展开。将查询反转，在母系树根路径上跑AC状态，再按失败链接累积访问次数；另需控制百万级转移和树遍历内存。'),
        204306: (2600, ['Manacher', '离线查询', '树状数组'], 'n和Q各二十万，查询任意区间包含的回文出现总数。二次区间DP不适用，需对回文半径在查询两边界裁剪后的贡献做离线分解与多种前缀计数，而非仅计算整串半径和。'),
        19786: (2900, ['回文自动机', '字符串计数'], '二十万长度，选择两个可重叠子串按顺序拼成回文并计位置方案。需联合回文前后缀与跨串匹配计数；全同字符时方案为全部子串数的平方，答案也会超过64位。'),
        236911: (2600, ['回文自动机', '动态规划'], '多组总长二百万，选三个互不相交回文最大化长度和，需按位置的多阶段DP与回文后缀转移优化；最长单回文及最长相邻双回文不足以独立求解此约束。'),
    }
    for number, (rating, topics, reason) in reviews.items():
        review_rating(number, rating, reason, knowledge=topics)
    review_rating(236739, 2900, '已逐条核对为CF932G Palindrome Partition，同为百万长度偶数串、偶数段且镜像段相同的划分计数；Codeforces当前官方数值评级2900，超过2300。',
                  origin={'url': 'https://codeforces.com/problemset/problem/932/G', 'rating': 2900,
                          'ratingVerifiedAt': '2026-11-08', 'platform': 'Codeforces'}, estimate=False)


if __name__ == '__main__':
    run()
    print('Recorded nine fully reviewed above-cutoff string tasks.')
