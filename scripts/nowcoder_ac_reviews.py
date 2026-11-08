"""Reviewed all AC-list statements, including duplicate cross-list tasks."""
from nowcoder_editorials import problem, review_rating, sha, statement


def run():
    for number, source_id, reason in [
        (234273, 'luogu-training-P5357', '同为二次加强版；允许重复模式，总模式长二十万、文本二百万，分别计重叠出现次数。'),
        (20155, 'luogu-training-P4052', '相同JSOI文本生成器；六十个大写词、长度各一百，文本长一百，答案模10007。'),
        (234268, 'luogu-training-P4052', '相同生成器计数规则，唯目标文本长度放宽至一万；需AC状态上的禁词DP，不低于原题映射档。'),
        (50358, 'luogu-training-P2444', '相同二进制病毒串、总长三万；AC自动机去掉危险状态后判断从根可达的有向环。'),
        (20366, 'luogu-training-P3311', '相同幸运数定义；上界1200位、模式总长1500，含前导零的模式也必须正确处理，AC加数位DP。'),
        (235605, 'luogu-training-CF547E', '相同CF547E；总字符串长二十万、五十万区间查询，计指定模式在编号区间中的出现总数。'),
    ]:
        source = problem(source_id)
        review_rating(number, source['difficulty'], reason + ' 沿用ToBe已有同题分制映射，明确标为估分，不作为牛客官方数值评级。',
                      origin={'id': source_id, 'url': source['url'], 'difficultySource': source.get('difficultySource'),
                              'sourceStatementSha256': sha(statement(source_id)['markdown'])})
    review_rating(14612, 2600, '字典动态只增、总字符串三百万，查询所有已加入模式的带重叠出现总数。需离线AC失败树欧拉序与子树加/单点查，或二进制分组维护多个AC，不能每次重建。在静态AC2400映射之上增加动态权重与多组内存控制，按2600估分。', knowledge=['AC自动机', '树状数组', '离线处理'])
    review_rating(233977, 2400, '词长总和与文本各三十万，允许重叠覆盖且每个词可重复使用。需AC失败转移传播最长匹配，再按右端点统计可覆盖区间，以区间覆盖贪心求最少词；普通切词DP不符合可重叠规则。依ToBe静态AC基础档2400估分。', knowledge=['AC自动机', '区间覆盖', '贪心'])


if __name__ == '__main__':
    run()
