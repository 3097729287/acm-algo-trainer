"""Full-statement difficulty reviews; source mappings are explicitly estimates."""
from nowcoder_editorials import problem, review_rating, sha, statement


def run():
    counterparts = {
        20079: ('luogu-training-P3203', '相同正数向右跳转、零起算下标、单点修改与跳出次数；n<=200000、m<=100000均一致。可分块维护或使用动态树。'),
        20311: ('luogu-training-P2147', '相同初始空森林，Connect/Destroy/Query动态连通性；n<=10000、m<=200000，所有删边合法且无环，输出Yes/No。'),
        17858: ('luogu-training-P2387', '相同双边权瓶颈和最小路径，允许自环与重边；需枚举第一权上界并动态维护第二权最小瓶颈森林。'),
        237650: ('luogu-training-P3804', '一百万小写字符，求重复子串长度乘出现次数最大值；需后缀结构构造、按长度归并endpos计数及64位贡献。'),
        237304: ('luogu-training-P2408', '同为本质不同子串计数；牛客省去n输入且把长度从十万放宽至一百万。后缀数组LCP或SAM状态长度差均适用，数据更大不降低原映射档。'),
    }
    for number, (source_id, evidence) in counterparts.items():
        source = problem(source_id)
        review_rating(number, source['difficulty'], evidence + ' 沿用ToBe已存同题的CF-EQ映射档；这是映射估分，不是牛客官方数值评级。',
                      origin={'id': source_id, 'url': source['url'],
                              'difficultySource': source.get('difficultySource'),
                              'sourceStatementSha256': sha(statement(source_id)['markdown'])})
    reviews = {
        237661: (2700, ['后缀自动机', '出现次数'], '长度250000，要求对所有子串长度输出最大出现次数。需SAM克隆状态与endpos逆长度传播，再将状态的长度上界贡献向较短长度传递；复杂度与同题库2700档SAM计数模板接近。'),
        237662: (2800, ['后缀自动机', '倍增'], '长度和询问各250000，需定位任意区间子串对应SAM状态，再回答endpos出现次数；前缀终态、suffix link倍增及长度区间匹配组合。'),
        237664: (2700, ['后缀自动机', '动态规划'], 'Typewriter，长度200000，复制必须来自已经输出的完整前缀且不可越界重叠。需求每个位置可复制的最长历史匹配，再与逐字输入做线性DP或区间最值优化，不能用允许自重叠的普通最长匹配替代。'),
        237666: (3000, ['后缀自动机', '可持久化线段树'], '长度及询问200000，目标是指定模式子串在另一个区间内完整出现次数；需子串状态定位和endpos位置范围计数，常见SAM加倍增与可持久化/合并线段树，明显超过2300。'),
        237308: (2400, ['后缀自动机', '子串计数'], '两个串各500000，要求本质不同公共子串数量而非仅最长长度。需SAM状态中匹配长度沿链接传播，再按状态长度区间扣重求和，或等价后缀数组计数；在ToBe不同子串计数2400档上增加公共性限制。'),
        15414: (2800, ['后缀自动机', 'Sprague-Grundy函数'], '多组目标串十万，全部输入长度三千万；每次从一个模式向右扩展且仍须为目标子串，多个独立游戏需SAM转移DAG上的SG值再异或，兼有字符串状态合并与组合博弈证明。'),
        226924: (2400, ['李超线段树', '动态凸包'], '二十万次任意斜率直线插入与区间[1,1000000]单点最大/最小查询；需维护上下包络，常规为两棵李超线段树或全动态凸壳，不能按插入顺序假设斜率单调。'),
        212927: (2800, ['CDQ分治', '动态规划', '李超线段树'], '网格总格数十万，事件可跳过，收益由上一个已触发位置的buff与曼哈顿步数决定。转移同时受行列偏序与斜率收益影响，需偏序DP配合直线最值结构/CDQ，不能每格只保留单一当前得分。'),
        237306: (2200, ['后缀数组', '最长公共子串'], '两个串各五十万，可拼接后构造后缀数组与LCP，扫描来自不同源串的相邻后缀最大公共前缀；需要线性内存和计数排序倍增实现。'),
        237667: (2300, ['后缀数组', '滑动窗口'], '多达十万模式，总长度一百万。拼接不同分隔符后用后缀数组、含全部源串的窗口和LCP单调队列，或用最短串SAM逐串匹配。需控制复杂度随总长增长，按2300边界纳入。'),
        229662: (1800, ['最近公共祖先', '倍增'], '树结构固定，仅查询根变化；以固定根求lca(x,y)、lca(x,root)、lca(y,root)，选固定根深度最大的一个，无须动态树。十万结点长链用迭代预处理。'),
        20325: (1800, ['树状数组', '离线查询'], '按备注更大范围支持一百万长度及询问。查询按右端点排序，树状数组只在每种颜色最后出现处保留一，区间和给不同种类数。'),
    }
    for number, (rating, topics, reason) in reviews.items():
        review_rating(number, rating, reason, knowledge=topics)


if __name__ == '__main__':
    run()
    print('Reviewed seventeen full statements; four are eligible and still need articles.')
