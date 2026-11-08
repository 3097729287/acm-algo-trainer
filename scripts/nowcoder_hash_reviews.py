"""The two remaining nontrivial tasks in the hash practice list."""
from nowcoder_editorials import problem, review_rating, sha, statement


def run():
    source = problem('luogu-training-P5685')
    review_rating(20200, source['difficulty'], '完整题意、五万长度上限与PUPPY/PUPPUP样例相同：统计两个串中相同回文的出现位置对。需将共享回文状态的两串出现次数分别传播并乘积计数，沿用ToBe2700的同题CF-EQ映射，非牛客官方评级。',
                  origin={'id': source['id'], 'url': source['url'], 'difficultySource': source.get('difficultySource'),
                          'sourceStatementSha256': sha(statement(source['id'])['markdown'])})
    review_rating(20224, 2500, '长度十万，两个串以同一下标j的两个字符同时保留再拼接，最优扭动串可长于单串；需分别处理中心落在一侧与跨拼接边界、回文半径与两串交叉匹配延伸。原站补充的N=1相同字符答案2等边界不能按两个独立回文简单合并。', knowledge=['Manacher', '字符串匹配', '最长公共前缀'])


if __name__ == '__main__':
    run()
    print('Recorded two full above-cutoff hash-list reviews.')
