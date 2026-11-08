"""Explicit counterpart reviews. A matching name alone is never sufficient."""
from nowcoder_editorials import CONTENT, alias, read


# Both complete statements, bounds and output contract were read. The source
# rating remains a reviewed/model-derived ToBe rating, not a Nowcoder rating.
PAIRS = {
    16421: ('luogu-training-P3954', '同一 NOIP 成绩题；权重为 2:3:5，输入为十的倍数，整数公式与范围一致。'),
    16658: ('luogu-training-P1085', '七天课时之和超过八才不高兴；并列保留最早一天，输入输出及范围相同。'),
    16617: ('luogu-training-P1055', 'ISBN 的九位加权校验、模十一与 X 编码相同，输出 Right 或更正后的完整号码。'),
    21469: ('luogu-training-P5015', '同一 NOIP 标题统计题；只统计非空格、非换行字符，输入输出合同一致。'),
    16490: ('luogu-training-P2669', '第 k 档连续发 k 天、每天 k 枚，前 K 天金币和；K 不超过一万，与来源一致。'),
    16705: ('luogu-training-P1035', '调和级数首次严格大于 K 的项数，K 最大为十五；浮点累加和停止条件一致。'),
    16622: ('luogu-training-P1067', '按降幂输出非零项、首项符号、系数一与常数项规则完全相同，n 最大一百。'),
    16649: ('luogu-training-P1047', '整数点零到 L 均有树，闭区间重复删除只计一次；L 最大一万，输入输出一致。'),
    14320: ('luogu-training-P5732', '均输出杨辉三角前 n 行；牛客放宽到 n=34，第 34 行最大数为 1166803110，原程序的整数类型可容纳。'),
    16669: ('luogu-training-P1059', '相同的 NOIP 随机数去重排序题，先输出不同元素数，再输出有序序列。'),
    16625: ('luogu-training-P1068', '相同 NOIP 面试线题；floor(1.5m) 位置分数，同分全部入选，成绩降序与报名号升序。'),
    16639: ('luogu-training-P1093', '相同 NOIP 奖学金题；总分、语文、学号三关键字，前五名，人数及成绩范围一致。'),
    16613: ('luogu-training-P1125', '只在出现过的字母中取最大最小频率，差为质数时输出 Lucky Word；长度小于一百。'),
    16692: ('luogu-training-P1030', '字母互异的二叉树中序与后序恢复先序，结点不超过八，输入顺序一致。'),
    16426: ('luogu-training-P1563', '玩具顺序、朝向与左右转向编码相同；按当前玩具朝向与指令确定模 n 的方向。'),
    16464: ('luogu-training-P2615', '奇数阶幻方逐步右上移动，已占用则向下；相同 NOIP 规则与矩阵输出。'),
    16618: ('luogu-training-P1056', '相同 NOIP 座椅题；独立统计横纵缝隙的冲突对，选取指定条数并按位置升序输出。'),
    20565: ('luogu-training-P2564', '生日礼物按颜色给坐标，要求覆盖全部颜色的最短坐标区间；同位置允许多珠，输入输出一致。'),
    16693: ('lab:luogu:P1049', '相同装箱问题；体积容量两万，三十个物品各取至多一次，输出最少剩余容量。'),
    16650: ('lab:luogu:P1048', '相同 NOIP 采药；每株一次，总时间一千，物品一百，输出最大价值。'),
    16666: ('lab:luogu:P1060', '相同 NOIP 开心的金明；每件一次，价值为价格乘重要度，无附件依赖。'),
    16645: ('luogu-training-P1005', '相同 NOIP 矩阵取数；每行独立从两端取，第 t 次乘二的 t 次方，需超过 64 位的整数。'),
    16590: ('luogu-training-P1541', '相同 NOIP 乌龟棋；四种步长卡片的使用次数构成状态，起点计分且所有卡片用完。'),
    16670: ('luogu-training-P1063', '相同 NOIP 能量项链；环上相邻合并，能量由三个边界标记相乘，取最大值。'),
    16576: ('luogu-training-P1077', '相同 NOIP 摆花；种类按编号固定顺序、每种数量有上限，方案数模 1000007。'),
    16641: ('luogu-training-P1095', '相同 NOIP 守望者；跑十七、闪六十耗十魔、休息回四，每次整秒，先判最早逃出时间。'),
    16679: ('luogu-training-P1038', '相同 NOIP 分层有向无环神经网络；仅正状态传播，非输入层扣阈值，按编号输出激活的输出点。'),
    20115: ('luogu-training-P3243', '相同 HNOI 菜肴制作，目标为小编号的完成位置优先；反图大根堆拓扑再逆序，含重边及多组数据。'),
    16889: ('luogu-training-P1196', '相同 NOI 银河英雄传说；整列接到队尾、查询两船之间数目，三万船和五十万指令。'),
    20245: ('luogu-training-P2330', '相同 SCOI 繁忙的都市；连通图用 n-1 条边，最小化所选边的最大权。'),
    235246: ('luogu-training-P1650', '相同田忌赛马的单组输入；每匹一次，胜负各二百，平局零，输出最高总收益。'),
    282494: ('luogu-training-P1908', '严格逆序对，n 最大五十万；牛客允许负数，归并比较不依赖非负取值，仍适用。'),
    19945: ('luogu-training-P4124', '相同 CQOI 手机号码；十一位无前导零，至少三连且不同时有四和八，区间计数。'),
    20268: ('luogu-training-P2657', '相同 windy 数的原始范围：二十亿以内，无前导零且相邻数位差至少二。'),
    20263: ('luogu-training-P2473', '相同 SCOI 奖励关；先见到随机宝物再决定吃不吃，可重复出现、前提只需曾吃过，n≤15、k≤100。'),
    19975: ('luogu-training-P4289', '相同 HAOI 移动玩具；4×4 的零一棋盘，交换四邻接的玩具与空格，求最少步数。'),
    207759: ('luogu-training-P2895', '相同 USACO 流星雨模型；仅第一象限、落点及四邻点永久损坏，必须严格早于撞击到达，逃到永久安全点。'),
    24587: ('luogu-training-P2212', '同一 USACO Watering the Fields；只允许平方距离至少 C 的边，n≤2000，输出 MST 权和或负一。'),
    24605: ('luogu-training-P1825', '同一 USACO Corn Maze；字母传送点成对、踏入必须瞬移且不额外耗时，边界与起终点字符一致。'),
    24734: ('luogu-training-P2986', '同一 USACO Great Cow Gathering；十万点带权树、每点牛数，输出加权距离和最小值，需 64 位。'),
    24851: ('luogu-training-P2639', '同一 USACO Bessie Weight Problem；各草捆仅一次，容量四万五，求最大不超过容量的总重。'),
    24948: ('luogu-training-P2419', '同一 USACO Cow Contest；胜负传递、无矛盾，能与其余所有牛比较的牛名次唯一。'),
    25044: ('luogu-training-P2879', '同一 USACO Tallest Cow；可见关系使两端之间严格矮，重复关系去重，差分求各牛最大可能高度。'),
    50528: ('luogu-training-P1886', '相同滑动窗口，n≤一百万；先输出每窗最小再输出最大，数值范围与单调双端队列兼容。'),
    51001: ('luogu-training-P1886', '同一 POJ Sliding Window 的英文原题；窗口及输入输出顺序与中文版本一致。'),
    50959: ('luogu-training-P1719', '同一最大非空子矩形和，牛客 n≤100、元素可全负；行压缩与非空最大子段和适用。'),
    16752: ('luogu-training-P1019', '相同 NOIP 单词接龙；每个词至多两次，重叠必须非空且不能完全包含，给定起始字母。'),
    16758: ('luogu-training-P1019', '与 NC16752 的完整题面、边界、样例、逐词两次上限及非包含重叠规则一致。'),
    16810: ('luogu-training-P1020', '相同导弹拦截；输入到 EOF，一套高度不增，输出最长不增长度和最少不增链数；牛客 n≤十万需 nlogn。'),
    285790: ('luogu-training-P1067', '牛客新版同题；多项式输出各符号、省略一、指数与常数项规则相同，逐项检查过完整题面。'),
    285881: ('luogu-training-P1056', '牛客新版同题；教室通道计数、横纵独立选择与最终位置升序输出均一致。'),
}


if __name__ == '__main__':
    existing = read(CONTENT / 'reviewed.json') if (CONTENT / 'reviewed.json').exists() else {}
    added = 0
    for number, (source, reason) in PAIRS.items():
        if 'nowcoder-global::' + str(number) not in existing:
            alias(number, source, reason)
            added += 1
    print('Registered explicit counterpart reviews:', added)
