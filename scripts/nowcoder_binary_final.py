"""Remaining individually reviewed binary/ratio problems and a global arc bound."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(200211, 1500, ['二分答案', '整数不等式'], '两种配方分别消耗 (2,3) 与 (4,1) 件材料，最大化装备数量。',
        '假设共做 z 件，其中 q 件使用第二种配方，则材料用量为 2z+2q 与 3z-2q。因此 q 至少为 max(0,ceil((3z-y)/2))，至多为 min(z,floor((x-2z)/2))。先确保 x>=2z，再比较整数上下界是否相交即可判定。能做 z 件就能少做，二分最大 z，上界 min(x/2,y)。',
        r'''int tests; cin >> tests; while (tests--) { long long x, y; cin >> x >> y; auto possible = [&](long long count) { if (2 * count > x) return false;
                long long lower = max(0LL, (3 * count - y + 1) / 2), upper = min(count, (x - 2 * count) / 2); return lower <= upper; };
            long long low = 0, high = min(x / 2, y); while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low << '\n'; }''',
        '不能只看材料总数除五，配方需要满足两种材料各自的整数约束。例如 x=3、y=2 虽合计五件，却一件装备也做不了。',
        complexity=r'每组时间 $O(\log\min(x,y))$，额外空间 $O(1)$。',
        cases=[{'input': '3\n3 2\n2 3\n4 1', 'output': '0\n1\n1'}])
    put(20012, 1800, ['贪心', '前缀最大值', '数列生成'], '将生成序列改为不下降，最小化单个音符的最大改变量。',
        '若 i<j 且 A[i]>A[j]，两端各最多改 d 后仍要不下降，必须有 A[i]-A[j]<=2d。因此最大前后下降量 drop 给出下界 ceil(drop/2)。它也充分：令 B[i]=max(1,所有 j<=i 的 A[j]-d)，这样 B 单调不降；当 d 已覆盖最大下降量时，B[i] 不超过 A[i]+d，也不低于 A[i]-d。初始音符为正，后续若生成零，最大下降量已经保证 d 至少为一，所以正整数下界也能满足。\n\n只需流式生成序列、维护此前最大值与 drop，无须存五百万项或反复二分。多项式用秦九韶形式逐步取模，每个乘积都在 64 位范围内。',
        r'''long long n, sa, sb, sc, sd, first, mod; cin >> n >> sa >> sb >> sc >> sd >> first >> mod;
        auto f = [&](long long x) { return (((sa * x + sb) % mod * x + sc) % mod * x + sd) % mod; };
        long long previousPrevious = 0, previous = first, maximum = first, drop = 0;
        for (long long i = 2; i <= n; i++) { long long current = (f(previous) + f(previousPrevious)) % mod; drop = max(drop, maximum - current); maximum = max(maximum, current); previousPrevious = previous; previous = current; }
        cout << (drop + 1) / 2;''',
        '输入实际有七个数，题面“六个数”是笔误。给定的 A[1] 就是初始项，之后从 A[0]=0、A[1] 按递推生成。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(24017, 1400, ['二分答案', '贪心'], '用最多 K 个半径相同的爆炸闭区间覆盖数轴上所有草捆，求最小整数半径。',
        '排序后，半径 R 的爆炸最多覆盖长度 2R 的区间。每次取最左未覆盖点 x，把爆炸中心放在 x+R，使覆盖右端尽量到 x+2R；跳过这段内所有点。任何覆盖 x 的爆炸都不可能比这更向右，因此该贪心使用最少牛。次数不超过 K 则 R 可行，二分最小值。',
        r'''int n, k; cin >> n >> k; vector<long long> x(n); for (auto &v : x) cin >> v; sort(x.begin(), x.end()); auto possible = [&](long long radius) { int next = 0, used = 0;
            while (next < n) { if (++used > k) return false; long long right = x[next] + 2 * radius; while (next < n && x[next] <= right) next++; } return true; };
        long long low = 0, high = x.back() - x.front(); while (low < high) { long long mid = (low + high) / 2; if (possible(mid)) high = mid; else low = mid + 1; } cout << low;''',
        '爆炸中心不必是草捆位置。覆盖总长度为直径 2R，不是半径 R；一个点或已有足够多牛时允许 R=0。',
        complexity=r'时间 $O(n\log n+n\log X)$，空间 $O(n)$，$X$ 是坐标跨度。')
    disk = r'''struct Focus { long double x, y, length, angle; };
    struct Arc { long double left, right, lower; bool operator<(const Arc &other) const { return lower > other.lower; } };
    '''
    put(16746, 2300, ['计算几何', '分支定界', '全局优化'], '圆盘内移动，到边界可免费传到对径点，求两点间最短步行距离。',
        '最优路只需考虑零次或一次传送。若有连续两次传送 P→-P、Q→-Q，中间步行长度至少 |-P-Q|；直接在盘内从 P 走到 -Q 的长度相同，就能删掉这两次传送。反复消去即可。\n\n零次是直线距离；一次传送时，枚举圆周入口 P，代价为 |A-P|+|B+P|，也就是 P 到两个焦点 A、-B 的距离和。圆周上的函数不宜直接假定为单峰，这里使用可证明误差的分支定界：对任意角度弧段，分别求每个焦点到该弧段的最小距离，两者之和是整段代价的下界。单个最小距离若焦点的径向方向在弧内，就等于半径减焦点半径；否则取两个端点中较近的。\n\n用最小堆优先细分下界最小的弧段，中点实际代价更新当前最好值 best。下界不小于 best 的弧段可丢弃；当堆中最小下界与 best 相差已不超过所需容差时，真实最优值被夹在两者之间，精度得到保证。代码把误差目标设为题目容差的百分之一，并用径向点和直线路径先提供上界。',
        r'''long double radius, ax, ay, bx, by; cin >> radius >> ax >> ay >> bx >> by; const long double pi = acosl(-1.0L); long double turn = 2 * pi;
        auto focus = [&](long double x, long double y) { long double angle = atan2l(y, x); if (angle < 0) angle += turn; return Focus{x, y, hypotl(x, y), angle}; };
        Focus a = focus(ax, ay), b = focus(-bx, -by);
        auto distances = [&](long double angle) { long double x = radius * cosl(angle), y = radius * sinl(angle); return pair<long double,long double>{hypotl(x - a.x, y - a.y), hypotl(x - b.x, y - b.y)}; };
        auto cost = [&](long double angle) { auto [x, y] = distances(angle); return x + y; };
        auto bound = [&](long double left, long double right) { auto dl = distances(left), dr = distances(right); long double x = min(dl.first, dr.first), y = min(dl.second, dr.second);
            if (left <= a.angle && a.angle <= right) x = radius - a.length; if (left <= b.angle && b.angle <= right) y = radius - b.length; return max(0.0L, x) + max(0.0L, y); };
        long double best = min({hypotl(ax - bx, ay - by), cost(a.angle), cost(b.angle)}); priority_queue<Arc> queue;
        auto offer = [&](long double l, long double r) { long double lower = bound(l, r); if (lower < best) queue.push({l, r, lower}); };
        for (int i = 0; i < 32; i++) { long double l = turn * i / 32, r = turn * (i + 1) / 32; best = min(best, cost((l + r) / 2)); offer(l, r); }
        while (!queue.empty()) { Arc arc = queue.top(); if (best - arc.lower <= 1e-8L * max(1.0L, best)) break; queue.pop(); long double mid = (arc.left + arc.right) / 2; best = min(best, cost(mid)); offer(arc.left, mid); offer(mid, arc.right); }
        cout << fixed << setprecision(12) << best;''',
        '起终点在边界时，最短距离可能为零。所有候选路径都在凸圆盘内；弧段下界分别取两项的最小值，即使它们在不同位置达到，也仍是合法下界。',
        declarations=disk, complexity=r'设实际细分了 $K$ 个弧段，时间 $O(K\log K)$，空间 $O(K)$；停止依据上下界误差。', floating_output=True,
        cases=[{'input': '1000\n0 0\n1 0', 'output': '1.000000000000'}, {'input': '1000\n1000 0\n-1000 0', 'output': '0.000000000000'}])
    put(24622, 1900, ['二分答案', '贪心', '二维数组'], '先水平切为 A 条，每条独立竖切为 B 块，最大化所有块中的最少巧克力数。',
        '二分每块至少 target。对当前横条累计每列的巧克力，沿列从左到右累计到至少 target 就竖切一块；若可切出至少 B 块，这个横条就合格，立即在当前行后横切并清空列和。两层都采用最早可行的切点：巧克力非负，把切点向后拖只会占用后续可用的行或列，不会改善后续机会。能得到至少 A 个横条就成功。剩余列、剩余行并入各自最后一块即可。',
        r'''int rows, columns, a, b; cin >> rows >> columns >> a >> b; vector<vector<long long>> grid(rows, vector<long long>(columns)); long long total = 0; for (auto &row : grid) for (auto &x : row) { cin >> x; total += x; }
        auto possible = [&](long long target) { vector<long long> sums(columns); int strips = 0; for (const auto &row : grid) { for (int c = 0; c < columns; c++) sums[c] += row[c]; long long sum = 0; int pieces = 0;
                for (long long x : sums) { sum += x; if (sum >= target) { pieces++; sum = 0; } } if (pieces >= b) { strips++; if (strips >= a) return true; fill(sums.begin(), sums.end(), 0); } } return false; };
        long long low = 0, high = total / a / b; while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low;''',
        '每条横带的竖切位置可独立选择，不要求整块布朗尼使用相同竖线。target=0 时每块仍须非空，代码每列至多切出一块。',
        complexity=r'时间 $O(RC\log(H+1))$，空间 $O(RC)$，$H$ 为总巧克力数。')
    if 'nowcoder-global::20276' not in existing:
        reviewed_clone(20276, 287789, '原题面、坐标范围、三种速度、样例和两位小数输出均与同源SCOI2010传送带版本相同，已完整核对。')
    put(20439, 2000, ['前缀和', '枚举', '贪心'], '通过调拨或增派老师提前成绩公告，连同学生等待费用，最小化总不愉快度。',
        '枚举所有课程最迟在第 D 天公布。晚于 D 的课程共需 need=Σmax(b[i]-D,0) 单位提前量；早于 D 的课程允许被推迟 room=Σmax(D-b[i],0) 单位，仍不超过 D。若调拨单价 A 比增派 B 便宜，就优先用 min(need,room) 单位调拨，其余增派；否则全用增派。学生等待费用为 C*Σmax(D-t[i],0)。\n\n日期最大只有十万，可对 b 和 t 分别建立人数与日期和前缀，O(1) 求 need、room、等待天数，直接枚举 D=1 到 max(b)。超过原最迟日不会减少任何调整量，等待又只会增加，因此不需要。每个固定 D 的调整都能逐单位配对实现，取所有 D 的最小总费用就是答案。',
        r'''long long transfer, hire, wait; int n, m; cin >> transfer >> hire >> wait >> n >> m; const int limit = 100000;
        vector<long long> students(limit + 1), studentSum(limit + 1), courses(limit + 1), courseSum(limit + 1); for (int i = 0; i < n; i++) { int t; cin >> t; students[t]++; studentSum[t] += t; }
        int latest = 0; long long total = 0; for (int i = 0; i < m; i++) { int day; cin >> day; courses[day]++; courseSum[day] += day; total += day; latest = max(latest, day); }
        for (int day = 1; day <= limit; day++) { students[day] += students[day - 1]; studentSum[day] += studentSum[day - 1]; courses[day] += courses[day - 1]; courseSum[day] += courseSum[day - 1]; }
        long long answer = LLONG_MAX; for (long long day = 1; day <= latest; day++) { long long need = total - courseSum[day] - day * (m - courses[day]), room = day * courses[day] - courseSum[day];
            long long moved = transfer < hire ? min(need, room) : 0; long long cost = moved * transfer + (need - moved) * hire + (day * students[day] - studentSum[day]) * wait; answer = min(answer, cost); } cout << answer;''',
        '学生等待的是所有课程中的最晚公布日，不能按每门课分别计等待。调拨只能利用提前课程距离 D 的空余天数；把 A 与 B 比较后再决定是否值得调拨。',
        complexity=r'日期上限 $V=10^5$，时间 $O(n+m+V)$，空间 $O(V)$。')
    put(17400, 1700, ['01 分数规划', '二分答案'], '最多删 k 门课，最大化按学分加权的平均分。',
        '总能删满 k 门而不变差：保留多于 n-k 门时，其中至少有一门分数不高于当前加权均值，删去它不会降低均值。因此固定保留 keep=n-k 门。二分均分 x，每门打分 s[i]*(c[i]-x)，选最大的 keep 项；若和非负就能达到 x。和总学分始终为正，移项判定等价。',
        r'''int n, k; cin >> n >> k; int keep = n - k; vector<long double> credits(n), score(n), transformed(n); for (auto &x : credits) cin >> x; long double high = 0; for (auto &x : score) { cin >> x; high = max(high, x); }
        long double low = 0; for (int iteration = 0; iteration < 65; iteration++) { long double mid = (low + high) / 2; for (int i = 0; i < n; i++) transformed[i] = credits[i] * (score[i] - mid);
            if (keep < n) nth_element(transformed.begin(), transformed.begin() + keep, transformed.end(), greater<long double>()); if (accumulate(transformed.begin(), transformed.begin() + keep, 0.0L) >= 0) low = mid; else high = mid; } cout << fixed << setprecision(12) << low;''',
        '学分不同，不能简单删分数最低的 k 门或按未加权平均处理。k=0 时仍应保留全部课程。',
        complexity=r'固定 $K=65$ 轮，平均时间 $O(Kn)$，空间 $O(n)$。', floating_output=True)
    put(14662, 1700, ['01 分数规划', '二分答案'], '选恰好 k 个手办，求总价值除总花费的最大值的整数部分。',
        '按本题整数输出要求，二分整数比值 x。存在一组选 k 个满足总比值至少 x，等价于这些手办的 Σ(v[i]-x*c[i]) 非负。每轮取变换后分数最大的 k 项判定，寻找最大可行整数，正好就是最优实数比值的向下取整。全程整数运算，不需要先算浮点再转换。',
        r'''int tests; cin >> tests; while (tests--) { int n, k; cin >> n >> k; vector<long long> cost(n), value(n), score(n); for (int i = 0; i < n; i++) cin >> cost[i] >> value[i];
            int low = 0, high = 10000; while (low < high) { int mid = (low + high + 1) / 2; for (int i = 0; i < n; i++) score[i] = value[i] - mid * cost[i];
                if (k < n) nth_element(score.begin(), score.begin() + k, score.end(), greater<long long>()); if (accumulate(score.begin(), score.begin() + k, 0LL) >= 0) low = mid; else high = mid - 1; } cout << low << '\n'; }''',
        '这里输出整数部分，采用最大可行整数；不是四舍五入到最近整数。比值应是总价值除总花费，不能选单件比值前 k 项后取平均。',
        complexity=r'每轮平均线性选择，总平均时间 $O(n\log 10000)$，空间 $O(n)$。',
        cases=[{'input': '1\n1 1\n2 3', 'output': '1'}])


if __name__ == '__main__':
    run()
    print('Registered nine reviewed ratio and geometric articles.')
