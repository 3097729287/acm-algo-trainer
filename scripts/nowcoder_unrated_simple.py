"""Complete-statement counterpart reviews and remaining unrated simple tasks."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_kmp_support import PREFIX_FUNCTION


def run():
    existing = read(CONTENT / 'reviewed.json')
    for number, source, reason in [
        (16438,285821,'完整核对NOIP回文日期，四位非零首年、两个闭区间端点及公历闰年规则一致。'),
        (16561,285894,'同一国王游戏，国王固定第一，乘积除当前右手向下取整，千大臣、左右手小于一万，Python任意精度参考适用。'),
        (16593,285819,'同一NOIP铺地毯，闭矩形边界也覆盖、最后铺的优先，至多一万张地毯。'),
        (16644,285704,'同一NOIP字符串展开，p1类型、p2重复、p3方向及首尾减号、异类、相等、逆序规则全部核对一致。'),
        (17857,285912,'同一NOI起床困难综合症，AND/OR/XOR按位独立、输入攻击0到m且输出无此上界限制；三十位处理覆盖原十亿范围。'),
        (19916,287783,'同为CQOI2010扑克牌，一套至多一张Joker，每种牌与Joker数至五亿，缺口总量受Joker数和套数双重上限约束。'),
        (20032,285827,'同一HNOI激光炸弹，坐标0到5000、R为整数、边界不计。原坐标为整数，可将炸弹边界放在半整数处覆盖R个连续坐标，滚动二维带宽求和适用。'),
        (20241,285847,'同为两列扫雷，第二列无雷、约束左上左下及同行三格之和，n至一万，两种首雷状态即可确定全列。'),
        (207040,285845,'原版丢手绢，n个相邻正间隔围环，目标为顺逆较短距离的最大值，n十万、周长32位上限；64位双指针代码兼容。'),
        (20860,285908,'原版兔子区间密码，多组一万、区间端点至10^18，可重复选数，按l xor r最高不同位构造全一答案。'),
        (24724,287779,'同一USACO Chocolate Eating，隔夜向下减半、按顺序吃、每天最低快乐最大，并输出每块食用日；五万规模，SPJ验证继承。'),
        (25043,285898,'同一USACO Protecting Flowers，每牛T为单程时间、等待损伤D，运送往返耗2T，按T/D交叉乘积排序，输出总损伤。'),
    ]:
        if f'nowcoder-global::{number}' not in existing:
            reviewed_clone(number,source,reason)
    if 'nowcoder-global::235569' not in existing:
        reviewed_clone(235569,251558,'完整核对中文牛可乐与NCPC和Efficient Solutions相同严格支配规则、重复评分计重及全部样例，按此题每组结束后的空行要求调整输出。',
                       replacements={"        if (tc > 1)\n            cout << '\\n';\n":'',
                                     "        }\n    }\n    return 0;":"        }\n        cout << '\\n';\n    }\n    return 0;",
                                     '原题测试组之间空一行。':'每组结束后额外输出一个空行。'})
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(50937,1200,['中位数','贪心'],'数轴上放一个货仓，最小化到各店的距离总和。',
        '排序后将最左与最右两店配对。货仓放在这一对之间时，两段距离之和恒等于两店间距；放到区间外只会更大。所有配对区间的公共部分正是中位数位置（偶数时为中间两数之间），因此取任一中位数最优。计算到它的绝对距离总和。',
        r'''int n; cin >> n; vector<long long> a(n); for (auto &x : a) cin >> x; sort(a.begin(),a.end()); long long median = a[n / 2], answer = 0; for (long long x : a) answer += abs(x - median); cout << answer;''',
        '输出最小距离和，而非仓库坐标；总和可能超过32位。',complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(22096,800,['循环','格式化输出'],'多组输入边长n，打印第i行从1到i的数字三角形，每个数字后有空格。',
        '外层循环控制行号i从1到n，内层依次输出1到i，每个数字后输出一个空格，行末换行。读到文件结束即可处理全部组，不另加分隔空行。',
        r'''int n; while (cin >> n) for (int i = 1; i <= n; i++) { for (int value = 1; value <= i; value++) cout << value << ' '; cout << '\n'; }''',
        '这是打印图案题，不是求最大路径的数字三角形DP。n可以超过9，每项按整数正常输出。',complexity=r'每组输出 $O(n^2)$ 个数字，额外空间 $O(1)$。')
    put(19913,1700,['前缀和','中位数'],'1到n的排列，统计奇数长度连续段中位数为b的数量。',
        'b只出现一次，合格区间必含其位置p。将大于b的数记+1、小于b记−1，b记0，中位数为b恰是区间总和0，因为左右两类数量相等，也自然保证总长度为奇数。枚举从p往左扩展的平衡值，统计各值出现次数（含只留p的平衡0）；再从p向右扩展，当前平衡为x时，左侧需−x，将其频次加入答案。',
        r'''int n,b; cin >> n >> b; vector<int> a(n); int position = 0; for (int i = 0; i < n; i++) { cin >> a[i]; if (a[i] == b) position = i; } vector<long long> count(2 * n + 1); count[n] = 1; int balance = 0; for (int i = position - 1; i >= 0; i--) { balance += a[i] > b ? 1 : -1; count[n + balance]++; } long long answer = count[n]; balance = 0; for (int i = position + 1; i < n; i++) { balance += a[i] > b ? 1 : -1; answer += count[n - balance]; } cout << answer;''',
        '只统计平衡0，不要套用下中位数计数中的平衡0或1。先将空左侧计一次，避免漏掉从b开始的区间。',complexity=r'时间、空间均为 $O(n)$。')
    put(20862,1800,['KMP','字符串替换'],'从左到右把原文本中的A替换为B，替换结果不再参与匹配。',
        '对A求前缀函数，在原S上做KMP。每当匹配出完整A，输出上一次已处理末尾到本次匹配开头的原文，再输出B；将已处理位置移到此次匹配末尾之后，并把当前匹配长度清0。清0确保重叠在刚消耗A内部的出现不再使用。全部扫描完后输出剩余尾部。新输出的B从未送入匹配过程，所以不会递归替换。输出分段流式写，避免把可能远长于输入的结果整体放入内存。',
        r'''string s,a,b; cin >> s >> a >> b; auto pi = prefixFunction(a); int matched = 0; size_t written = 0; for (size_t i = 0; i < s.size(); i++) { while (matched && s[i] != a[matched]) matched = pi[matched - 1]; if (s[i] == a[matched]) matched++; if (matched == (int)a.size()) { size_t begin = i + 1 - a.size(); cout.write(s.data() + written,begin - written); cout << b; written = i + 1; matched = 0; } } cout.write(s.data() + written,s.size() - written);''',
        '按左到右不重叠替换，不能把产生的新字符再扫入KMP。若B很长，实际输出时间必须计入复杂度。',declarations=PREFIX_FUNCTION,
        complexity=r'输入总长 $L$、输出长 $R$，时间 $O(L+R)$，空间 $O(L)$。')
    put(16857,2000,['深度优先搜索','搜索剪枝'],'固定整数体积的多层圆柱蛋糕，半径和高度自下而上严格减小，最小化外表面积除以π。',
        '从最下层向上搜索剩余k层。半径、高度都至少k，否则放不下上面严格更小的k−1层。预处理最少体积Σ(i³)和最少侧面积Σ(2i²)，剩余体积不足或面积下界已不优就剪枝。侧面贡献为2rh，所有顶部和台阶水平面积会望远镜相消，合计只需最下层半径平方。\n\n若下一层半径至多R−1，则剩余体积V产生的侧面积至少ceil(2V/(R−1))，还可加强下界。枚举合法r、h并扣体积、加面积，层数归零且体积恰为0时更新答案。无可行结构输出0。',
        r'''int volume,layers; cin >> volume >> layers; vector<int> minVolume(layers + 1), minSide(layers + 1); for (int i = 1; i <= layers; i++) { minVolume[i] = minVolume[i - 1] + i * i * i; minSide[i] = minSide[i - 1] + 2 * i * i; } int best = 1000000000; auto dfs = [&](auto &&self, int remaining, int k, int maxRadius, int maxHeight, int area) -> void { if (k == 0) { if (remaining == 0) best = min(best,area); return; } if (remaining < minVolume[k] || area + minSide[k] >= best || maxRadius <= k || maxHeight <= k) return; if (area + (2 * remaining + maxRadius - 2) / (maxRadius - 1) >= best) return; int upperRadius = min(maxRadius - 1,(int)sqrt((remaining - minVolume[k - 1]) / k)); for (int r = upperRadius; r >= k; r--) { int upperHeight = min(maxHeight - 1,(remaining - minVolume[k - 1]) / (r * r)); for (int h = upperHeight; h >= k; h--) self(self,remaining - r * r * h,k - 1,r,h,area + 2 * r * h + (k == layers ? r * r : 0)); } }; dfs(dfs,volume,layers,(int)sqrt(volume) + 1,volume + 1,0); cout << (best == 1000000000 ? 0 : best);''',
        '不包括最底部下底面，水平外露总面积是底层半径平方，不能给每层都加一个顶面积。上下层的半径与高度都严格递减。',
        complexity=r'枚举合法递减半径、高度组合，为指数搜索；各层受体积和面积下界强剪枝。预处理和搜索栈空间 $O(M)$。')


if __name__ == '__main__':
    run()
