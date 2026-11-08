"""Array and matrix articles, with bounds and numerical stability reviewed."""
from nowcoder_editorials import add, CONTENT, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(205911, 1100, ['统计', '浮点运算'], '每组计算整数序列的极差与总体方差，方差保留三位小数。',
        '第一遍读取时求和、最大值与最小值，得到均值。第二遍累加每项与均值之差的平方，再除以 n。使用 long double，并按定义求偏差平方，避免“大数平方的平均值减均值平方”相消导致精度损失。',
        r'''int t; cin >> t; while (t--) { int n; cin >> n; vector<long long> a(n);
            long long lo = LLONG_MAX, hi = LLONG_MIN; long double sum = 0;
            for (long long &x : a) { cin >> x; sum += x; lo = min(lo, x); hi = max(hi, x); }
            long double mean = sum / n, variance = 0;
            for (long long x : a) { long double delta = x - mean; variance += delta * delta; }
            cout << hi - lo << ' ' << fixed << setprecision(3) << variance / n << '\n';
        }''', '题目使用总体方差，分母为 n 而非 n-1。所有数都相同时方差为零。',
        complexity='每组时间与数组空间均为 $O(n)$。', cases=[{'input': '1\n2\n999999999 1000000000', 'output': '1 0.250'}])
    put(16538, 900, ['枚举', '数位'], '统计一到 n 的十进制表示中，目标数字出现的总次数。',
        'n 最大一百万，直接枚举每个数，反复对十取余检查最低位，再整除十。每出现一次都计数，同一个数可以贡献多次。',
        r'''int n, digit; cin >> n >> digit; int ans = 0;
        for (int i = 1; i <= n; i++) for (int x = i; x > 0; x /= 10) if (x % 10 == digit) ans++; cout << ans;''',
        '不添加前导零；区间从一开始，数字零只在数的实际表示中计数。', complexity=r'时间 $O(n\log n)$，额外空间 $O(1)$。')
    put(22227, 1200, ['递推', '约瑟夫环'], '从编号 k 开始每报 m 淘汰一人，求零起始编号的最后幸存者。',
        '先按起点为零求幸存者。只有一人时下标为零；人数从 i-1 增加到 i 时，第一次出队后下一次报数起点为 m mod i，所以把旧幸存者位置加 m 再对 i 取余。最终再加初始起点 k，并对 n 取余。',
        r'''int n, k, m; cin >> n >> k >> m; int survivor = 0;
        for (int i = 2; i <= n; i++) survivor = (survivor + m) % i; cout << (survivor + k) % n;''',
        'k 位置报的是一而不是零；报 m 的人出队后，从下一人重新报一。', complexity='时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '5 4 1', 'output': '3'}])
    put(15431, 900, ['分支', '数列'], '给定若干天的月亮大小，判断下一天变大还是变小，无法判断则输出负一。',
        '最后一天为零时一定开始变大，为十五时一定开始变小。其余位置若至少记录两天，就沿用最后两天的增减趋势；若只记录一天且不在端点，两个方向都可能，输出负一。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x;
        if (a.back() == 0) cout << "UP"; else if (a.back() == 15) cout << "DOWN";
        else if (n == 1) cout << -1; else cout << (a[n - 1] > a[n - 2] ? "UP" : "DOWN");''',
        '记录只有一天时也可能可以判断，零与十五这两个端点应先处理。', complexity='时间与数组空间均为 $O(n)$。')
    put(15051, 1100, ['贪心', '位置'], '允许交换一次排列中的两个数，最大化一与 n 的下标差。',
        '若交换不同时涉及一与 n，最多只移动其中一个，另一个位置保持固定。移动的数放在距固定数最远的端点最好；若同时交换一与 n，两者距离不变。因此分别考虑固定一或固定 n 时到两个端点的距离，取四者最大。',
        r'''int n; cin >> n; int p = 1, q = 1;
        for (int i = 1; i <= n; i++) { int x; cin >> x; if (x == 1) p = i; if (x == n) q = i; }
        cout << max({p - 1, n - p, q - 1, n - q});''',
        '只有一次交换，一和 n 通常不能同时分别移到两端。n=1 时距离为零。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(18356, 1400, ['单调栈'], '对每个位置，求右侧第一个严格更大元素的下标，没有则为零。',
        '从右往左维护候选栈。处理 a[i] 时，栈顶若不大于 a[i] 就弹出：它既不满足当前查询，也会被更近且不小的 a[i] 取代。弹完后栈顶就是最近的严格更大位置，再把 i 入栈。每个位置只进出栈一次。',
        r'''int n; cin >> n; vector<int> a(n), ans(n), st; for (int &x : a) cin >> x;
        for (int i = n - 1; i >= 0; i--) { while (!st.empty() && a[st.back()] <= a[i]) st.pop_back(); ans[i] = st.empty() ? 0 : st.back() + 1; st.push_back(i); }
        for (int i = 0; i < n; i++) { if (i) cout << ' '; cout << ans[i]; }''',
        '相等的值也必须弹出，因为要求严格大于。最后按一行输出，返回一开始的下标。', complexity='时间与数组空间均为 $O(n)$。',
        cases=[{'input': '4\n2 2 2 2', 'output': '0 0 0 0'}])
    put(208813, 1000, ['枚举', '逆序对'], '统计前面元素严格大于后面元素的有序位置对数。',
        '本题 n 不超过两千，可以直接枚举 i<j 的每一对，若 a[i]>a[j] 就计数。每对只在它的前后下标被枚举时出现一次，不会重复。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; long long ans = 0;
        for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) if (a[i] > a[j]) ans++; cout << ans;''',
        '相同元素不构成逆序对。这里按两千的范围选双循环，不能照搬到五十万规模的逆序对模板。',
        complexity='时间 $O(n^2)$，数组空间 $O(n)$。', cases=[{'input': '3\n1 1 1', 'output': '0'}])
    put(213401, 1000, ['计数', '集合交'], '求所有受访学生都喜欢的课程数量。',
        '为每门课程记录被多少名学生喜欢。每名学生的列表只贡献一次，全部读取后，计数等于 N 的课程恰好属于所有学生的交集。',
        r'''int n, m; cin >> n >> m; vector<int> count(m + 1);
        for (int i = 0; i < n; i++) { int k; cin >> k; vector<bool> seen(m + 1);
            while (k--) { int x; cin >> x; if (!seen[x]) { seen[x] = true; count[x]++; } } }
        int ans = 0; for (int x = 1; x <= m; x++) if (count[x] == n) ans++; cout << ans;''',
        '某名学生喜欢零门课时结果必为零。统计的是课程种数，不是喜欢次数之和。', complexity='时间 $O(NM)$，额外空间 $O(M)$。')
    put(218048, 1000, ['进制转换', '整数运算'], '把两数的二进制数码当成十进制数字串，再按十进制加法相加。',
        '逐位取原数的二进制位，但使用十进制位权一、十、一百等累加，得到对应的十进制整数。对两项分别转换后直接相加。原数最多十六个二进制位，因此转换值可由 long long 容纳。',
        r'''int a, b; cin >> a >> b;
        auto convert = [](int x) { long long value = 0, place = 1; while (x) { value += (x & 1) * place; place *= 10; x >>= 1; } return value; };
        cout << convert(a) + convert(b);''',
        '不能直接计算 a+b 再转二进制。结果中出现数字二是正常的，不按二进制进位。', complexity=r'时间 $O(\log\max(A,B))$，额外空间 $O(1)$。',
        cases=[{'input': '32768 32768', 'output': '2000000000000000'}])
    put(25322, 900, ['去重', '标记数组'], '保留每个数第一次出现的位置，按原顺序输出去重序列。',
        '用 seen[x] 记录此前是否输出过该数，依输入顺序扫描。未出现过时输出并打标记，出现过则跳过。这样既去重又保留第一次出现的顺序。',
        r'''int n; cin >> n; bool seen[5001] = {}; bool first = true;
        for (int i = 0; i < n; i++) { int x; cin >> x; if (!seen[x]) { if (!first) cout << ' '; cout << x; first = false; seen[x] = true; } }''',
        '不能排序后再去重，因为题目要求原输入顺序。', complexity='时间 $O(n+U)$，标记数组空间 $O(U)$，其中 $U=5000$。')
    put(25320, 900, ['有序数组', '二分'], '将一个整数插入升序序列，并保持有序。',
        'lower_bound 找到第一个不小于 x 的位置，把 x 插在它之前。若所有元素都小于 x，就在末尾插入；空数组时该位置也自然是末尾。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; int x; cin >> x;
        a.insert(lower_bound(a.begin(), a.end(), x), x);
        for (int i = 0; i <= n; i++) { if (i) cout << ' '; cout << a[i]; }''',
        '二分只负责找位置；vector 插入仍需要移动后面的元素。', complexity=r'查找 $O(\log n)$、移动与输出 $O(n)$，总时间与数组空间为 $O(n)$。',
        cases=[{'input': '0\n8', 'output': '8'}])
    put(22210, 900, ['素数', '筛法'], '按递增顺序输出一到 N 的全部素数。',
        '先把二到 N 标为可能素数。从小到大遇到未被删去的 p，就删除 p²、p²+p 等倍数；更小的倍数已经由更小因子处理过。最后输出未被删去的数。',
        r'''int n; cin >> n; vector<bool> prime(n + 1, true); prime[0] = false; if (n >= 1) prime[1] = false;
        for (int p = 2; p <= n / p; p++) if (prime[p]) for (int x = p * p; x <= n; x += p) prime[x] = false;
        bool first = true; for (int x = 2; x <= n; x++) if (prime[x]) { if (!first) cout << ' '; cout << x; first = false; }''',
        '一不是素数，N=1 时应没有数字输出。', complexity=r'时间 $O(N\log\log N)$，筛数组空间 $O(N)$。')
    put(54580, 1000, ['筛法', '前缀和'], '多次查询不超过 n 的素数个数。',
        '先筛出一千以内的素数，再令 prefix[i]=prefix[i-1]+isPrime[i]。每个查询直接输出 prefix[n]，所有查询共享一次预处理。',
        r'''const int limit = 1000; vector<bool> prime(limit + 1, true); prime[0] = prime[1] = false;
        for (int p = 2; p <= limit / p; p++) if (prime[p]) for (int x = p * p; x <= limit; x += p) prime[x] = false;
        int prefix[limit + 1] = {}; for (int i = 1; i <= limit; i++) prefix[i] = prefix[i - 1] + prime[i];
        int t; cin >> t; while (t--) { int n; cin >> n; cout << prefix[n] << '\n'; }''',
        '查询包含 n 本身；n=1 时答案为零。', complexity=r'预处理 $O(U\log\log U)$，每次查询 $O(1)$，空间 $O(U)$，$U=1000$。')
    put(25323, 1000, ['双指针', '归并'], '把两个升序序列合成一个升序序列，保留重复值。',
        '各用一个指针指向当前未取的最小元素，比较后取较小者并只移动它的指针。一边用完后，依次取另一边剩余元素。每次输出的都是全部未输出元素中的最小值。',
        r'''int n, m; cin >> n >> m; vector<int> a(n), b(m); for (int &x : a) cin >> x; for (int &x : b) cin >> x;
        int i = 0, j = 0; bool first = true;
        while (i < n || j < m) { int x; if (j == m || (i < n && a[i] <= b[j])) x = a[i++]; else x = b[j++];
            if (!first) cout << ' '; cout << x; first = false; }''',
        '合并不等于去重；两个相等元素都需要输出。条件短路保证不会读取越界元素。', complexity='时间与数组空间均为 $O(n+m)$。')
    put(54155, 800, ['二维数组'], '读入矩阵后，查询一开始编号的第 x 行第 y 列。',
        '按行列保存全部数据，再把输入的一开始坐标减一，访问 a[x-1][y-1]。',
        r'''int n, m; cin >> n >> m; vector<vector<int>> a(n, vector<int>(m));
        for (auto &row : a) for (int &x : row) cin >> x; int x, y; cin >> x >> y; cout << a[x - 1][y - 1];''',
        '行号在前、列号在后，不能交换 x 和 y。', complexity='时间与存储空间均为 $O(nm)$。')
    put(54159, 800, ['二维数组', '分支'], '判断主对角线下方的元素是否全为零。',
        '按行列读取，每遇到 i>j 的位置就检查它是否为零。如果有非零值，最终输出 NO；否则输出 YES。对角线及上方没有限制。',
        r'''int n; cin >> n; bool ok = true; for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) {
            int x; cin >> x; if (i > j && x != 0) ok = false; } cout << (ok ? "YES\n" : "NO\n");''',
        '上三角矩阵不要求对角线为一，也不要求对角线上方非零。', complexity='时间 $O(n^2)$，额外空间 $O(1)$。')
    put(52069, 1000, ['二维数组', '枚举'], '地雷保留星号，其他格输出八邻域中的地雷数。',
        '保存原棋盘。对每个非雷格，枚举行偏移和列偏移各为负一、零、一的九种组合，排除自身和越界位置，统计原棋盘中的雷。输出过程中不修改原棋盘，避免把已填的数字误当成输入。',
        r'''int n, m; cin >> n >> m; vector<string> a(n); for (string &s : a) cin >> s;
        for (int i = 0; i < n; i++) { for (int j = 0; j < m; j++) {
            if (a[i][j] == '*') { cout << '*'; continue; } int count = 0;
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) {
                int x = i + dx, y = j + dy; if (dx == 0 && dy == 0) continue;
                if (x >= 0 && x < n && y >= 0 && y < m && a[x][y] == '*') count++;
            } cout << count;
        } cout << '\n'; }''',
        '斜向四格也在邻域中；边界处要先检查坐标再访问。', complexity='时间与棋盘空间均为 $O(nm)$。',
        cases=[{'input': '1 1\n.', 'output': '0'}, {'input': '1 1\n*', 'output': '*'}])
    put(13883, 1400, ['时间戳', '矩阵'], '多次把整行或整列赋值，输出最后矩阵。',
        '每个格子的最终值只由它所在行的最后赋值与所在列的最后赋值中较晚者决定。分别保存每行、每列的最后时间和数值，操作时只更新一个记录。最后枚举格子比较两个时间。未修改的时间与值均为零。',
        r'''int t; cin >> t; while (t--) { int n, q; cin >> n >> q;
            vector<int> rt(n), ct(n), rv(n), cv(n);
            for (int time = 1; time <= q; time++) { int op, k, v; cin >> op >> k >> v; k--;
                if (op == 1) { rt[k] = time; rv[k] = v; } else { ct[k] = time; cv[k] = v; } }
            for (int i = 0; i < n; i++) { for (int j = 0; j < n; j++) { if (j) cout << ' '; cout << (rt[i] > ct[j] ? rv[i] : cv[j]); } cout << '\n'; }
        }''', '不能逐次改整行整列，二十万次操作乘五百会造成不必要的开销。最终输出矩阵本身已需 n² 次。',
        complexity='每组时间 $O(q+n^2)$，额外空间 $O(n)$。')
    put(54160, 800, ['二维数组'], '将 n 行 m 列矩阵转置成 m 行 n 列。',
        '原来的第 i 行第 j 列成为转置后的第 j 行第 i 列。所以输出时外层枚举原列 j，内层枚举原行 i，依次输出 a[i][j]。',
        r'''int n, m; cin >> n >> m; vector<vector<int>> a(n, vector<int>(m)); for (auto &row : a) for (int &x : row) cin >> x;
        for (int j = 0; j < m; j++) { for (int i = 0; i < n; i++) cout << a[i][j] << ' '; cout << '\n'; }''',
        '转置只是行列互换，不是顺时针旋转；输出共有 m 行。', complexity='时间与数组空间均为 $O(nm)$。')
    put(15426, 1300, ['对称', '数学'], '顺序填入一到 n² 的奇数阶矩阵，只保留连接四边中点围成的菱形，求和。',
        '菱形关于中心对称，每对相对元素之和为 n²+1，中心元素为 (n²+1)/2。若半径 r=(n-1)/2，菱形元素数是 1+4(1+…+r)=(n²+1)/2。因此所有元素的平均值与元素个数相同，答案是 ((n²+1)/2)²。',
        r'''int t; cin >> t; while (t--) { long long n; cin >> n; long long middle = (n * n + 1) / 2; cout << middle * middle << '\n'; }''',
        'n 可接近一万，不能真的建矩阵；答案约为 n⁴/4，需要 long long。', complexity='每组时间与额外空间均为 $O(1)$。')
    put(16121, 1400, ['不变量', '网格'], '每个空格至少有两个已感染四邻格才感染，初始感染数 m 严格小于边长 n，问能否铺满。',
        '考虑所有感染格组成图形的周长。初始每格至多贡献四条边，总周长至多 4m。新增格与 k≥二个感染邻格相接，周长变化为 4-2k≤零，所以周长不可能增大。整个 n×n 方格的周长为 4n，但 m<n 导致初始周长严格小于 4n，因此无论初始位置如何都不可能铺满，只能输出 NO。',
        r'''int n, m; cin >> n >> m; for (int i = 0; i < m; i++) { int x, y; cin >> x >> y; } cout << "NO";''',
        '结论使用了当前题面 m<n 的严格限制，不能推广成“任意初始感染都不可能铺满”。不需要分配一百万格或逐轮模拟。',
        complexity='读完输入时间 $O(m)$，额外空间 $O(1)$。')
    put(207419, 1000, ['矩阵', '模拟'], '把字符方阵顺时针旋转九十度后输出。',
        '旋转后第 i 行来自原矩阵第 i 列，且原行号从 n-1 递减到零。因此输出 b[i][j]=a[n-1-j][i]，无需另建结果矩阵。',
        r'''int n; cin >> n; vector<string> a(n); for (string &s : a) cin >> s;
        for (int i = 0; i < n; i++) { for (int j = 0; j < n; j++) cout << a[n - 1 - j][i]; cout << '\n'; }''',
        '顺时针旋转不等于转置，原矩阵左下角应成为输出左上角。', complexity='时间与棋盘空间均为 $O(n^2)$。')


if __name__ == '__main__':
    run()
    print('Registered array and matrix editorials.')
