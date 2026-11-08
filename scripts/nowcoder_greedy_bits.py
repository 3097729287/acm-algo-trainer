"""Reviewed matrix enumeration, exchange arguments and bitwise decisions."""
from nowcoder_editorials import CONTENT, add, add_python, read, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(285890, 1800, ['状态压缩', '枚举', '贪心'], '用 k 次整行或整列清零，最大化覆盖到的矩阵权值和，每格只计一次。',
        '枚举选中的行集合。已选行的权值直接加入，剩下各列的新增收益，就是这列中未选行的总和；再选收益最大的 k-已选行数 列即可。任何行列方案都会对应某个枚举行集合，所以不会漏最优解。若 k 已至少为行数，直接选全部行便能获得总和，后续回合可重复清零，不会扣分。',
        r'''int n, m, k; cin >> n >> m >> k; vector<vector<long long>> a(n, vector<long long>(m)); long long total = 0; for (auto &row : a) for (auto &x : row) { cin >> x; total += x; }
        if (k >= min(n, m)) { cout << total; return 0; } long long answer = 0;
        for (int mask = 0; mask < (1 << n); mask++) { int used = __builtin_popcount((unsigned)mask); if (used > k) continue; vector<long long> columns(m); long long score = 0;
            for (int r = 0; r < n; r++) for (int c = 0; c < m; c++) { if (mask >> r & 1) score += a[r][c]; else columns[c] += a[r][c]; }
            sort(columns.begin(), columns.end(), greater<long long>()); for (int c = 0; c < min(m, k - used); c++) score += columns[c]; answer = max(answer, score); }
        cout << answer;''',
        '不能每轮贪心选当前最大行列，两个选择会重叠。固定行集合后，列之间没有交集，此时取最大若干列才是安全的贪心。',
        complexity=r'时间 $O(2^n(nm+m\log m))$，空间 $O(nm+m)$。')
    put(285316, 1400, ['贪心', '排序'], '安排所有活动，最小化最大超时扣分。',
        '按截止时间从早到晚做。若相邻两活动先做截止晚的 B、再做截止早的 A，交换它们后，A 更早完成，B 的新完成时间等于原 A 的完成时间，而 B 的截止时间更晚，因此这两项的最大超时不会增加。不断消除逆序即得到截止时间顺序。累加用时，记录 max(0,完成时刻-截止时间)。',
        r'''int n; cin >> n; vector<pair<long long,long long>> tasks(n); for (auto &[deadline, cost] : tasks) cin >> cost >> deadline; sort(tasks.begin(), tasks.end());
        long long time = 0, answer = 0; for (auto [deadline, cost] : tasks) { time += cost; answer = max(answer, time - deadline); } cout << answer;''',
        '目标是最大扣分最小，不是总扣分最小，也不是按活动耗时排序。完成时刻与截止时刻相等不扣分。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    if 'nowcoder-global::285894' not in existing:
        add_python(285894, 1900, ['贪心', '排序', '高精度'], '重排大臣，使前缀左手乘积除以当前右手数所得奖赏的最大值尽量小。',
            '按每位大臣左右手乘积 l*r 递增排序。对相邻 A、B，设进入它们前的左手乘积为 P；若 lA*rA<=lB*rB，则顺序 A、B 中的两项 P/rA、P*lA/rB 都不大于顺序 B、A 中的 P*lB/rA，或被其最大项覆盖，因此交换为乘积升序不会增加最大奖赏。两人之后的前缀乘积不变，交换论证可逐步推广到全队。遍历排序结果，先以当前前缀除右手数更新最大值，再把当前左手数乘进前缀。Python 整数可直接保存约四千位的乘积。',
            '''import sys

data = list(map(int, sys.stdin.buffer.read().split()))
n = data[0]
product = data[1]
ministers = [(data[3 + 2 * i], data[4 + 2 * i]) for i in range(n)]
ministers.sort(key=lambda pair: pair[0] * pair[1])
answer = 0
for left, right in ministers:
    answer = max(answer, product // right)
    product *= left
print(answer)
''', '国王固定在最前，不参与排序；国王右手数不用于任何大臣的分母。当前大臣的左手数只能在算完他的奖赏后乘入。',
            complexity=r'排序 $O(n\log n)$；若最大乘积有 $D$ 位，遍历约 $O(nD)$ 次位运算量，额外空间 $O(n+D)$。',
            cases=[{'input': '1\n9999 1\n9999 2', 'output': '4999'}])
    put(285898, 1500, ['贪心', '排序'], '每次赶回一头牛，其他牛在往返时间内吃花，最小化总损失。',
        '两头牛 A、B 相邻时，先 A 后 B 会额外让 B 等待 2tA，反序则让 A 等待 2tB；其他牛的等待总时长不变。所以 A 放前更好当且仅当 tA*dB<=tB*dA。按该交叉乘积规则排序，维护之前已用的总时间 elapsed，当前牛贡献 elapsed*d，随后时间增加 2t。',
        r'''int n; cin >> n; vector<pair<long long,long long>> cows(n); for (auto &[t, d] : cows) cin >> t >> d;
        sort(cows.begin(), cows.end(), [](const auto &a, const auto &b) { return a.first * b.second < b.first * a.second; });
        long long elapsed = 0, answer = 0; for (auto [t, d] : cows) { answer += elapsed * d; elapsed += 2 * t; } cout << answer;''',
        '当前正在被赶走的牛不再吃花，所以它只贡献此前等待时间。不要用浮点除法比较比值。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(285910, 1600, ['位运算', '贪心'], '在闭区间 [l,r] 中找二进制一最多的整数。',
        '从 x=l 开始，x|(x+1) 会把最低的零位改为一，同时把更低位补成一，是从当前形态继续增加一位一所需的最小增量。若结果仍不大于 r 就采用，否则停止。也可以理解为逐渐把 l 的低位后缀补满：想在更高零位处改一，就先付出比填较低零位更大的增量，因此停止时区间里不会存在一更多的数。',
        r'''int t; cin >> t; while (t--) { unsigned long long l, r; cin >> l >> r; unsigned long long x = l; while ((x | (x + 1)) <= r) x |= x + 1; cout << x << '\n'; }''',
        '允许输出任意最优整数，无须恰等于样例。范围含零且可达 10^18，使用 64 位整数。',
        complexity=r'每组最多处理六十个零位，时间 $O(\log r)$，额外空间 $O(1)$。',
        checker='maximum-popcount-in-interval', cases=[{'input': '4\n0 0\n8 10\n15 16\n6 6', 'output': '0\n9\n15\n6'}])
    put(18979, 1600, ['位运算', '前缀和'], '每次查询选一个最小的非负 31 位整数 x，最大化区间内各数与 x 异或的总和。',
        '每个二进制位独立贡献。若该位原数组中零更多，令 x 的该位为一，就让更多结果位为一；若一更多，令 x 该位为零。两种数量相同则收益相同，为使 x 最小应选零。预处理每一位上一的前缀数量，每次查询在三十一位分别比较。',
        r'''int n; cin >> n; vector<array<int,31>> prefix(n + 1); prefix[0].fill(0);
        for (int i = 1; i <= n; i++) { int x; cin >> x; for (int b = 0; b <= 30; b++) prefix[i][b] = prefix[i - 1][b] + (x >> b & 1); }
        int q; cin >> q; while (q--) { int l, r; cin >> l >> r; long long answer = 0; for (int b = 0; b <= 30; b++) { int ones = prefix[r][b] - prefix[l - 1][b]; if (2 * ones < r - l + 1) answer |= 1LL << b; } cout << answer << '\n'; }''',
        '即使 a[i] 小于 2^30，x 仍允许第 30 位为一；必须检查零到三十共三十一位。平票时选零。',
        complexity=r'时间 $O(31(n+q))$，空间 $O(31n)$。')
    put(285908, 1500, ['位运算', '数学'], '从同一闭区间中选两整数，使它们的异或最大。',
        '若 l=r，只能得到零。否则令 k 为 l 与 r 最高的不同位：所有区间数在更高位都相同，所以异或不超过低 k+1 位全一。去掉公共前缀，区间跨过第 k 位的零一边界；边界前一个数是 0 后接 k 个一，边界数是 1 后接 k 个零，两者都在区间中，异或达到 2^(k+1)-1。计算 l^r 的位数后输出同位数全一即可。',
        r'''int t; cin >> t; while (t--) { unsigned long long l, r; cin >> l >> r; auto different = l ^ r; unsigned long long answer = 0; while (different) { answer = answer * 2 + 1; different >>= 1; } cout << answer << '\n'; }''',
        '可以选相同的两个数，单点区间答案为零。这里输出最大异或值，不需要输出选中的两个整数。',
        complexity=r'每组时间 $O(\log r)$，额外空间 $O(1)$。')
    put(285912, 1800, ['位运算', '贪心'], '初始攻击值在零到 m 内，经过同一组 AND、OR、XOR 后最大化最终值。',
        '位运算不会在各位间传递影响。让初始数分别为全零和低三十位全一，跑完全部操作，即同时得到每一位输入零或一时的最终结果。再从高到低构造输入：若输入零就能让结果位为一，优先选零以节约额度；否则只有输入一能改善结果且累计输入仍不超过 m 时才选一。高位结果比所有低位之和更重要，当前保留更小输入又给后续留下最多选择，所以此贪心成立。',
        r'''int n; long long m; cin >> n >> m; long long zero = 0, one = (1LL << 30) - 1;
        for (int i = 0; i < n; i++) { string op; long long t; cin >> op >> t; if (op == "AND") { zero &= t; one &= t; } else if (op == "OR") { zero |= t; one |= t; } else { zero ^= t; one ^= t; } }
        long long input = 0, answer = 0; for (int b = 29; b >= 0; b--) { long long bit = 1LL << b; if (zero & bit) answer |= bit; else if ((one & bit) && input + bit <= m) { input += bit; answer |= bit; } } cout << answer;''',
        '上限限制的是初始输入，不是最终输出。相同结果时选输入零，不能浪费额度。',
        complexity=r'时间 $O(n+\log m)$，额外空间 $O(1)$。')
    if 'nowcoder-global::24636' not in existing:
        reviewed_clone(24636, 285338, '完整题面与闭整数区间删除相同，但 L<=10^8、M<=10^6；逐点标记不适用，已核对区间合并的64位实现可覆盖该范围。', rating=1400,
                       replacements={'长度十亿': '长度上亿'})
    put(14683, 1700, ['前缀和', '数学'], '查询将区间 [l,r] 的带权货物运到指定点 x 的距离费用，答案取模。',
        '先由相邻距离得到各点坐标 p[i]，预处理重量前缀 B 与坐标乘重量前缀 W。把查询在 x 处分成两半：左侧费用为 p[x]*重量和-坐标重量和，右侧为坐标重量和-p[x]*重量和。区间端点取与 [l,r] 的交，x 在区间外时一侧为空即可。只做加减乘且最终取模，坐标和两个前缀都可边算边取模，避免真实加权总量溢出。',
        r'''const long long mod = 1000000007; int n, m; cin >> n >> m; vector<long long> p(n + 1), b(n + 1), w(n + 1);
        for (int i = 2; i <= n; i++) { long long distance; cin >> distance; p[i] = (p[i - 1] + distance) % mod; }
        for (int i = 1; i <= n; i++) { long long weight; cin >> weight; weight %= mod; b[i] = (b[i - 1] + weight) % mod; w[i] = (w[i - 1] + p[i] * weight) % mod; }
        auto sum = [&](const vector<long long> &prefix, int l, int r) { return l > r ? 0LL : (prefix[r] - prefix[l - 1] + mod) % mod; };
        while (m--) { int x, l, r; cin >> x >> l >> r; long long answer = 0; int end = min(r, x), start = max(l, x + 1);
            if (l <= end) answer = (p[x] * sum(b, l, end) - sum(w, l, end)) % mod;
            if (start <= r) answer = (answer + sum(w, start, r) - p[x] * sum(b, start, r)) % mod;
            cout << (answer + mod) % mod << '\n'; }''',
        '真实坐标乘重量会超出 long long，不能先求完整费用再取模。分左右依据原下标，不能比较已取模的坐标。',
        complexity=r'预处理 $O(n)$，每次询问 $O(1)$，空间 $O(n)$。')
    put(202498, 1700, ['区间合并', '差分', '排序'], '多次把某种货物放进连续仓库，求拥有不同货物种类最多的最小仓库编号。',
        '同一种货物重复覆盖同一仓库只算一种。先按货物编号、区间左端点排序，把每种货物的覆盖区间合并为互不重叠的段。对每个合并段 [l,r] 做差分 +1：d[l]++、d[r+1]--。最后前缀累加就是各仓库的种类数，从左到右仅在严格更大时更新答案。',
        r'''int n, m; cin >> n >> m; vector<tuple<int,int,int>> intervals; for (int i = 0; i < m; i++) { int l, r, kind; cin >> l >> r >> kind; if (l > r) swap(l, r); intervals.push_back({kind, l, r}); } sort(intervals.begin(), intervals.end());
        vector<int> difference(n + 2); int kind = -1, left = 0, right = -1; auto flush = [&]() { if (left <= right) { difference[left]++; difference[right + 1]--; } };
        for (auto [d, l, r] : intervals) { if (d == kind && l <= right + 1) right = max(right, r); else { flush(); kind = d; left = l; right = r; } } flush();
        int count = 0, best = -1, answer = 1; for (int i = 1; i <= n; i++) { count += difference[i]; if (count > best) { best = count; answer = i; } } cout << answer;''',
        '直接对每条进货区间加一会把同种货物重复计算。需要先分货物做区间并集，再跨货物累加。',
        complexity=r'时间 $O(m\log m+n)$，空间 $O(n+m)$。')
    put(14583, 1900, ['前缀和', '贪心', '倒序扫描'], '两组糖糖依次消灭前方能力更弱的异组者，期间有全已出现前缀加一，求最终存活数。',
        '令 P[t] 为时刻不超过 t 的加一操作次数。第 j 个糖糖在第 i 秒开始时（j<i）的能力是 b[j]+P[i-1]-P[j-1]，新来的 i 尚未获得以前的加成，能力是 b[i]。故 j 会被 i 消灭当且仅当两者异组且 b[j]-P[j-1]<b[i]-P[i-1]。把每个能力改写成这个固定值后，从右向左维护两组后缀最大值；当前不小于异组最大值才可存活。即使后面的某个糖糖最终也死了，它此前的消灭已经发生，仍需参与最大值。',
        r'''int tests; cin >> tests; while (tests--) { int n, m; cin >> n >> m; vector<int> group(n + 1), boost(n + 1); vector<long long> strength(n + 1);
            for (int i = 1; i <= n; i++) cin >> group[i] >> strength[i]; for (int i = 0; i < m; i++) { int t; cin >> t; boost[t]++; }
            long long elapsed = 0; for (int i = 1; i <= n; i++) { strength[i] -= elapsed; elapsed += boost[i]; }
            long long maximum[2] = {LLONG_MIN, LLONG_MIN}; int answer = 0; for (int i = n; i >= 1; i--) { if (strength[i] >= maximum[group[i] ^ 1]) answer++; maximum[group[i]] = max(maximum[group[i]], strength[i]); } cout << answer << '\n'; }''',
        '加成发生在当秒结束后，所以固定值减的是 P[i-1]。能力相等不会消灭，判断必须保留等号。',
        complexity=r'每组时间 $O(n+m)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
    print('Registered twelve reviewed greedy and bitwise articles.')
