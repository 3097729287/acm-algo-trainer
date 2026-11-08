"""Individually reviewed recurrences and prefix sums from contest 19851."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(16642, 1400, ['递推', '高精度'], '把每种大小各两个的 n 层圆盘从 A 柱移到 C 柱，求最少移动次数。',
        '要移动最下面的两个最大盘，必须先把所有较小盘搬到另一根柱上，再用两步把最大盘移到目标柱，最后搬回小盘，得到 A[n]=2A[n-1]+2，A[0]=0。这个过程可以实现；反过来，在第一个最大盘离开起点和最后一个最大盘到达终点之间，小盘必须让出相应的柱子，因此不能少于这两次小盘转移与两次最大盘移动。递推也给出 A[n]=2^(n+1)-2。n 可达二百，直接用十进制数组反复乘二加二。',
        r'''int n; cin >> n; vector<int> a(1, 0);
        for (int i = 0; i < n; i++) { int carry = 2; for (int &digit : a) { int value = digit * 2 + carry; digit = value % 10; carry = value / 10; }
            while (carry) { a.push_back(carry % 10); carry /= 10; } }
        for (int i = (int)a.size() - 1; i >= 0; i--) cout << a[i];''',
        '同尺寸的两个盘允许叠放，且彼此不区分；不能按普通的 2n 个不同盘套 2^(2n)-1。数组最低位在前，输出时反向。',
        complexity=r'答案有 $O(n)$ 位，时间 $O(n^2)$，额外空间 $O(n)$。',
        cases=[{'input': '200', 'output': str(2 ** 201 - 2)}])
    put(14975, 1000, ['递推', '线性 DP'], '用长度为一或二的方块铺满长度 n 的盒子，统计铺法。',
        '按最后一块分类：它长一，前面有 f[n-1] 种；它长二，前面有 f[n-2] 种。两类互不重叠，所以 f[n]=f[n-1]+f[n-2]。令 f[0]=1，表示空前缀只有一种铺法，f[1]=1。一次预处理到八十，再回答各组询问。',
        r'''long long f[81] = {1, 1}; for (int i = 2; i <= 80; i++) f[i] = f[i - 1] + f[i - 2];
        int t; cin >> t; while (t--) { int n; cin >> n; cout << f[n] << '\n'; }''',
        '铺法区分方块的排列顺序。f[80]=37889062373143906，需要 long long，但不需要取模或高精度。',
        complexity=r'预处理时间与空间 $O(80)$，每个询问 $O(1)$。',
        cases=[{'input': '1\n80', 'output': '37889062373143906'}])
    put(205036, 1500, ['计数 DP', '递推'], '统计每行恰有一个黑格、转置后不变的 n 阶零一矩阵。',
        '矩阵对称使每列也恰有一个黑格。考察第 n 行：若黑格在对角线 (n,n)，剩下 f[n-1] 种；否则它在第 j 列，对称性强迫 (j,n) 为黑，两行两列都已确定，j 有 n-1 种，剩下 f[n-2] 种。因此 f[n]=f[n-1]+(n-1)f[n-2]，边界 f[0]=f[1]=1。只保存相邻两项。',
        r'''const long long mod = 1000000007; int n; cin >> n; long long previous = 1, current = 1;
        for (int i = 2; i <= n; i++) { long long next = (current + (i - 1LL) * previous) % mod; previous = current; current = next; } cout << current;''',
        '横竖一致指关于主对角线转置相等，不要求关于水平中线或竖直中线对称。乘法在 long long 中计算后取模。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '1', 'output': '1'}, {'input': '4', 'output': '10'}])
    put(208910, 1000, ['前缀和'], '多次查询静态整数数组的闭区间和。',
        '令 prefix[i] 是前 i 个数之和，prefix[0]=0。区间 [L,R] 恰好等于前 R 项去掉前 L-1 项，所以答案为 prefix[R]-prefix[L-1]。数组没有修改，预处理一次即可。',
        r'''int n, m; cin >> n >> m; vector<long long> prefix(n + 1);
        for (int i = 1; i <= n; i++) { long long x; cin >> x; prefix[i] = prefix[i - 1] + x; }
        while (m--) { int l, r; cin >> l >> r; cout << prefix[r] - prefix[l - 1] << '\n'; }''',
        '负数同样适用；前缀和的绝对值可达 10^10，必须使用 long long。L=1 时自然减去 prefix[0]。',
        complexity=r'总时间 $O(N+M)$，空间 $O(N)$。',
        cases=[{'input': '3 3\n-100000 0 100000\n1 3\n1 1\n2 3', 'output': '0\n-100000\n100000'}])
    put(22197, 1000, ['枚举', '计数'], '把 n 元换成一元、二元、五元，统计各种面额数量的组合。',
        '枚举五元的张数 five，剩余 rest=n-5five。二元可以取零到 floor(rest/2) 张，而一元数量随之唯一确定。因此这一轮贡献 floor(rest/2)+1 种，求和即可。',
        r'''int n; cin >> n; int answer = 0; for (int five = 0; five * 5 <= n; five++) answer += (n - five * 5) / 2 + 1; cout << answer;''',
        '只区分各面额的数量，不区分拿钱的先后顺序；循环必须包含一种面额完全不用的情况。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '1', 'output': '1'}, {'input': '5', 'output': '4'}])
    put(18264, 1400, ['数学', '递推', '字符串'], '给出可能有一百万位的 n，求 F[n-1]F[n+1]-F[n]^2。',
        '记要求的式子为 D[n]。用 F[n+1]=F[n]+F[n-1]，可得 D[n+1]=F[n]F[n+2]-F[n+1]^2=F[n]^2-F[n-1]F[n+1]=-D[n]。而 D[2]=1，所以 D[n]=(-1)^n。根本不必算斐波那契数，只需读入十进制 n，判断末位奇偶。',
        r'''string n; cin >> n; cout << ((n.back() - '0') % 2 == 0 ? 1 : -1);''',
        'n 本身也超出整数类型，不能用 long long 或把 n 转成普通整数。字符串读入的时间随位数增长。',
        complexity=r'设输入有 $L$ 位，时间与保存输入的空间均为 $O(L)$。',
        cases=[{'input': '2', 'output': '1'}, {'input': '999999999999999999999999999999999999999999', 'output': '-1'}])
    put(19244, 1100, ['排序', '分组'], '查询某个月日生日的人中，年龄第 k 大者的名字。',
        '用日期对一万取余得到月日，把朋友按月日分组。每组按完整出生日期从小到大排序，出生越早年龄越大；查询 (k,s) 直接输出 s 组的第 k-1 项。题目保证日期不重复且询问有答案。',
        r'''int n, m; cin >> n >> m; map<int, vector<pair<int, string>>> groups;
        for (int i = 0; i < n; i++) { string name; int date; cin >> name >> date; groups[date % 10000].push_back({date, name}); }
        for (auto &[day, people] : groups) sort(people.begin(), people.end());
        while (m--) { int k, day; cin >> k >> day; cout << groups[day][k - 1].second << '\n'; }''',
        '输入询问的顺序是 k、月日。用 cin 读入十进制整数 0220 会得到 220，和分组键一致，不要把它手写为 C++ 八进制常量。',
        complexity=r'排序总时间 $O(n\log n)$，每次定位分组 $O(\log n)$，空间 $O(n)$。')
    put(15036, 1000, ['递推'], '按题给模式补全数列，并回答多个下标询问。',
        '题目采用的延伸规律是从第四项开始，每项等于前三项之和：2=0+1+1，4=1+1+2，7=1+2+4，后面的已知项也都吻合。以 a[1]=0、a[2]=a[3]=1 预处理到第五十项；不断读 n 直到文件结束。',
        r'''long long a[51] = {}; a[2] = a[3] = 1; for (int i = 4; i <= 50; i++) a[i] = a[i - 1] + a[i - 2] + a[i - 3];
        int n; while (cin >> n) cout << a[n] << '\n';''',
        '这里没有开头的测试组数。有限个前缀本不能唯一确定无限数列，这里按出题所用的三项递推理解。结果需要 long long。',
        complexity=r'预处理时间、空间 $O(50)$，每次查询 $O(1)$。',
        cases=[{'input': '10\n4', 'output': '81\n2'}])


if __name__ == '__main__':
    run()
    print('Registered eight reviewed recurrences.')
