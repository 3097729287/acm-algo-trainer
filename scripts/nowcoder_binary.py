"""Reviewed binary search and convex geometric optimization."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(285318, 1100, ['排序', '二分查找'], '查询数组中值位于闭区间 [l,r] 的元素个数。',
        '先排序。lower_bound(l) 指向第一个不小于 l 的数，upper_bound(r) 指向第一个大于 r 的数，两迭代器之差就是闭区间内的元素数。重复元素按出现次数统计。',
        r'''int n, q; cin >> n >> q; vector<int> a(n); for (int &x : a) cin >> x; sort(a.begin(), a.end());
        while (q--) { int l, r; cin >> l >> r; cout << (l > r ? 0 : upper_bound(a.begin(), a.end(), r) - lower_bound(a.begin(), a.end(), l)) << '\n'; }''',
        '区间限制的是值，不是原数组下标。右端使用 upper_bound 才能包含等于 r 的所有值。',
        complexity=r'排序 $O(n\log n)$，每次询问 $O(\log n)$，空间 $O(n)$。')
    put(287777, 1100, ['前缀和', '二分查找'], '按各音符持续拍数，查询零起算时刻正在播放哪个音符。',
        'prefix[i] 为前 i 个音符的总拍数，第 i 个音符占据 [prefix[i-1],prefix[i])。给定 t，找第一个严格大于 t 的结束时间，它的下标就是答案。严格比较恰好把切换时刻归到下一个音符。',
        r'''int n, q; cin >> n >> q; vector<long long> prefix(n + 1); for (int i = 1; i <= n; i++) { int duration; cin >> duration; prefix[i] = prefix[i - 1] + duration; }
        while (q--) { long long t; cin >> t; cout << upper_bound(prefix.begin() + 1, prefix.end(), t) - prefix.begin() << '\n'; }''',
        't 从零开始，音符编号从一开始。不能在 t 恰等于 prefix[i] 时继续返回第 i 个音符。',
        complexity=r'预处理 $O(n)$，每次查询 $O(\log n)$，空间 $O(n)$。')
    put(287779, 1800, ['二分答案', '贪心', '构造'], '顺序吃巧克力，隔夜快乐减半，最大化 d 天结束时的最低快乐并给出吃法。',
        '二分每天最低值 target。判定时按天模拟，先将上一天快乐减半，再按原顺序吃到至少 target 就停，把未必需要的巧克力留到以后。提前多吃只会让它的贡献在夜晚减半，延后到真正需要时不会更差，所以这种最晚食用的贪心判定充分。若巧克力耗尽仍不足就失败。目标越小越容易，二分上界可取全部快乐总和。最后按最优值重跑并记录食用日期；剩余巧克力全部放在末日，保证每块都有安排，也不会降低最低值。',
        r'''int n, days; cin >> n >> days; vector<long long> a(n); long long total = 0; for (auto &x : a) { cin >> x; total += x; }
        vector<int> plan(n); auto possible = [&](long long target, bool record) { long long happiness = 0; int next = 0;
            for (int day = 1; day <= days; day++) { happiness /= 2; while (happiness < target && next < n) { happiness += a[next]; if (record) plan[next] = day; next++; } if (happiness < target) return false; }
            if (record) while (next < n) plan[next++] = days; return true; };
        long long low = 0, high = total; while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid, false)) low = mid; else high = mid - 1; }
        possible(low, true); cout << low << '\n'; for (int day : plan) cout << day << '\n';''',
        '同一天可以吃零块或多块。隔夜减半必须向下取整；日程应保持原巧克力顺序，任意最优日程均可。',
        complexity=r'总快乐为 $H$，时间 $O((n+d)\log(H+1))$，空间 $O(n)$。', checker='chocolate-eating-schedule',
        cases=[{'input': '1 3\n1', 'output': '0\n3'}, {'input': '2 1\n2 3', 'output': '5\n1\n1'}])
    put(251604, 1600, ['折半枚举', '排序', '双指针'], '四列各选一个元素，统计四项和为零的不同下标四元组。',
        '枚举前两列所有 n² 个和放入 left，后两列同理放入 right，分别排序。一个指针从 left 最小值出发，另一个从 right 最大值出发：和为负就增大左指针，和为正就减小右指针；和为零时统计两边当前值各自的重复次数，乘起来加入答案，再跳过整组重复值。每组下标选择恰对应一次和的配对。',
        r'''int n; cin >> n; vector<array<int,4>> a(n); for (auto &row : a) for (int &x : row) cin >> x; vector<int> left, right; left.reserve((size_t)n * n); right.reserve((size_t)n * n);
        for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) { left.push_back(a[i][0] + a[j][1]); right.push_back(a[i][2] + a[j][3]); } sort(left.begin(), left.end()); sort(right.begin(), right.end());
        int i = 0, j = (int)right.size() - 1; long long answer = 0; while (i < (int)left.size() && j >= 0) { long long sum = (long long)left[i] + right[j]; if (sum < 0) i++; else if (sum > 0) j--; else { int x = left[i], y = right[j]; long long cx = 0, cy = 0; while (i < (int)left.size() && left[i] == x) { i++; cx++; } while (j >= 0 && right[j] == y) { j--; cy++; } answer += cx * cy; } } cout << answer;''',
        '和相同但下标不同也算不同四元组，不能只算不同数值。单个两数和可存 int，总方案数用 long long。',
        complexity=r'时间 $O(n^2\log n)$，空间 $O(n^2)$，两和数组在上限约占五十兆字节。')
    put(287783, 1700, ['二分答案', '贪心'], 'n 种普通牌与 m 张百搭牌，每套至多用一张百搭，最多组成多少套。',
        '若要组成 x 套，第 i 类普通牌的缺口为 max(0,x-c[i])，总缺口 need 必须不超过百搭总数 m，也必须不超过套数 x，因为每套至多一张百搭。条件也充分：给每个缺口安排不同的套，所有缺口总数不超过 x，不会让一套出现两个百搭；余下位置用对应普通牌填满。判定对 x 单调，可二分最大可行值。上界为所有牌数除以 n。',
        r'''int n; long long m; cin >> n >> m; vector<long long> count(n); long long total = m; for (auto &x : count) { cin >> x; total += x; }
        auto possible = [&](long long sets) { long long need = 0; for (long long x : count) { need += max(0LL, sets - x); if (need > m || need > sets) return false; } return true; };
        long long low = 0, high = total / n; while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low;''',
        '只比较缺口与 m 不够，还要比较缺口与套数；同一套中不能用两张 Joker。所有总量使用 long long。',
        complexity=r'最大可能套数为 $U$，时间 $O(n\log(U+1))$，空间 $O(n)$。')
    put(287785, 1800, ['二分答案', '差分'], '按订单先后借教室，求第一笔无法满足的订单；全可满足输出零。',
        '前 x 笔订单能否完成具有单调性。判定时把前 x 笔的闭区间需求用差分累加，再还原每天总需求，检查是否超过该日容量。二分最大的可行前缀长度 low；若 low=m 就无失败订单，否则首笔失败为 low+1。每次判定先清空差分。',
        r'''int n, m; cin >> n >> m; vector<long long> capacity(n + 1), difference(n + 2); for (int i = 1; i <= n; i++) cin >> capacity[i];
        struct Order { long long count; int left, right; }; vector<Order> orders(m); for (auto &o : orders) cin >> o.count >> o.left >> o.right;
        auto possible = [&](int count) { fill(difference.begin(), difference.end(), 0); for (int i = 0; i < count; i++) { auto o = orders[i]; difference[o.left] += o.count; difference[o.right + 1] -= o.count; }
            long long used = 0; for (int day = 1; day <= n; day++) { used += difference[day]; if (used > capacity[day]) return false; } return true; };
        int low = 0, high = m; while (low < high) { int mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << (low == m ? 0 : low + 1);''',
        '本版本失败时只输出申请人编号，与原 NOIP 版本的输出格式不同。每天总需求可达 10^15，差分使用 long long。',
        complexity=r'时间 $O((n+m)\log(m+1))$，空间 $O(n+m)$。')
    put(287787, 1900, ['二分答案', '双指针', '计数'], '所有长度至少 k 的子段各取第 k 大，求这些数中的第 m 大。',
        '二分候选值 x。某个子段的第 k 大至少为 x，当且仅当子段里至少有 k 个不小于 x 的数。扫描右端点，用左指针维护窗口中这类数少于 k：只要数量达到 k 就移出左端。此时起点为零到 left-1 的全部子段都曾包含至少 k 个，贡献 left 个。把每个右端的贡献相加，若至少为 m，说明最终第 m 大也至少为 x。目标值越大满足的子段越少，二分最大可行值。',
        r'''int tests; cin >> tests; while (tests--) { int n, k; long long m; cin >> n >> k >> m; vector<int> a(n); int high = 0; for (int &x : a) { cin >> x; high = max(high, x); }
            auto possible = [&](int value) { int left = 0, count = 0; long long segments = 0; for (int right = 0; right < n; right++) { count += a[right] >= value; while (count >= k) { count -= a[left] >= value; left++; } segments += left; } return segments >= m; };
            int low = 1; while (low < high) { int mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low << '\n'; }''',
        '要求的是两层第几大，不是第几小；判定使用大于等于以正确处理重复值。m 和子段数都可能超过有符号 int。',
        complexity=r'值域上限 $V$，时间 $O(n\log V)$，空间 $O(n)$。')
    put(277089, 2100, ['解析几何', '区间合并'], '行人按射线运动进入灯的感应圆，离开后延迟熄灭，求总亮灯时长。',
        '对每个行人，将给定方向单位化。把圆心相对起点的向量投影到方向上，得投影长度 projection；叉积绝对值是圆心到直线的垂距。若垂距超过半径，或投影在身后，则未来不会触圆。否则由勾股得到半弦长 half，进入、离开时刻分别为 (projection-half)/speed、(projection+half)/speed。包含边界，因此相切也触发。这个人的亮灯区间是 [进入,离开+延迟]。对所有这样的实数区间排序求并集长度，即总时长。',
        r'''long double x0, y0, radius, delay; int n; cin >> x0 >> y0 >> radius >> n >> delay; vector<pair<long double,long double>> intervals;
        for (int i = 0; i < n; i++) { long double xs, ys, xe, ye, speed; cin >> xs >> ys >> xe >> ye >> speed; long double dx = xe - xs, dy = ye - ys, length = hypotl(dx, dy); dx /= length; dy /= length;
            long double qx = x0 - xs, qy = y0 - ys, projection = qx * dx + qy * dy, perpendicular = fabsl(qx * dy - qy * dx); if (projection < 0 || perpendicular > radius + 1e-12L) continue;
            long double half = sqrtl(max(0.0L, radius * radius - perpendicular * perpendicular)); long double enter = max(0.0L, (projection - half) / speed), leave = (projection + half) / speed; if (leave >= 0) intervals.push_back({enter, leave + delay}); }
        sort(intervals.begin(), intervals.end()); long double answer = 0, left = 0, right = 0; bool started = false; for (auto [l, r] : intervals) { if (!started) { left = l; right = r; started = true; } else if (l <= right) right = max(right, r); else { answer += right - left; left = l; right = r; } } if (started) answer += right - left;
        cout << fixed << setprecision(12) << answer;''',
        '给出的第二个点只确定方向，行人会继续越过它。延迟加在离开时刻之后；不能把各人照明时长直接相加。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。', floating_output=True,
        cases=[{'input': '0 0 1\n1 2\n-2 1 0 1 1', 'output': '2.000000000000'}, {'input': '0 0 1\n1 2\n-2 0 -3 0 1', 'output': '0.000000000000'}])
    circles = r'''struct Point { long double x, y; };
    struct Circle { Point center; long double square; };
    long double distance2(Point a, Point b) { return (a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y); }
    Circle diameter(Point a, Point b) { Point center{(a.x + b.x) / 2, (a.y + b.y) / 2}; return {center, distance2(a, b) / 4}; }
    bool outside(Circle c, Point p) { return distance2(c.center, p) > c.square + 1e-12L * max(1.0L, c.square); }
    Circle through(Point a, Point b, Point c) {
        long double ux = b.x - a.x, uy = b.y - a.y, vx = c.x - a.x, vy = c.y - a.y, determinant = 2 * (ux * vy - uy * vx);
        if (fabsl(determinant) < 1e-18L) { Circle result = diameter(a, b), ac = diameter(a, c), bc = diameter(b, c); if (ac.square > result.square) result = ac; if (bc.square > result.square) result = bc; return result; }
        long double u2 = ux * ux + uy * uy, v2 = vx * vx + vy * vy; Point center{a.x + (u2 * vy - v2 * uy) / determinant, a.y + (ux * v2 - vx * u2) / determinant}; return {center, distance2(center, a)};
    }'''
    put(285572, 2200, ['计算几何', '随机增量法', '最小圆覆盖'], '求覆盖全部给定点的最小圆的半径与圆心。',
        '最小覆盖圆由至多三个边界点决定。随机打乱点，逐个加入；新点已在圆内就不变，否则它必须在新圆边界上，先把圆重置为这个点。重新扫描之前的点，若又遇到外点，就固定这两个点，先取它们为直径；继续检查更早的点，仍在圆外时，由三个边界点求外接圆。这是固定边界点数量逐层增加的增量算法，最多三层。随机顺序使触发重建的概率很小，期望线性。两点圆用中点，三点圆解垂直平分线的二元方程；共线时取最远两点为直径。',
        r'''int n; cin >> n; vector<Point> a(n); for (auto &p : a) cin >> p.x >> p.y; mt19937 generator(20261108); shuffle(a.begin(), a.end(), generator); Circle circle{a[0], 0};
        for (int i = 1; i < n; i++) if (outside(circle, a[i])) { circle = {a[i], 0}; for (int j = 0; j < i; j++) if (outside(circle, a[j])) { circle = diameter(a[i], a[j]); for (int k = 0; k < j; k++) if (outside(circle, a[k])) circle = through(a[i], a[j], a[k]); } }
        cout << fixed << setprecision(12) << sqrtl(circle.square) << '\n' << circle.center.x << ' ' << circle.center.y;''',
        '最小圆圆心一般不是点的算术平均值。共线点没有三点外接圆，必须处理；判断在圆内时用很小的容差，输出保留足够位数。', declarations=circles,
        complexity=r'随机顺序下期望时间 $O(n)$，最坏 $O(n^3)$；输入存储空间 $O(n)$。', floating_output=True,
        cases=[{'input': '3\n0 0\n2 0\n4 0', 'output': '2.000000000000\n2.000000000000 0.000000000000'}])
    put(287789, 2000, ['三分搜索', '凸函数', '计算几何'], '从 A 沿第一线段、转为平面行走，再沿第二线段到 D，最小化耗时。',
        '令离开第一线段的位置 E=A+t(B-A)，进入第二线段的位置 F=C+u(D-C)，t、u 都在零到一。耗时为 |AE|/p+|EF|/r+|FD|/q。固定 t 后，它对 u 是凸函数，可三分求最小；联合表达式是凸函数，对 u 取最小后的函数对 t 仍凸，因此外层再三分。每层固定迭代一百次，最后求值；两端位置也在闭区间中，无须额外假设最优在内部。',
        r'''long double ax, ay, bx, by, cx, cy, dx, dy, p, q, r; cin >> ax >> ay >> bx >> by >> cx >> cy >> dx >> dy >> p >> q >> r;
        auto inner = [&](long double t) { long double ex = ax + t * (bx - ax), ey = ay + t * (by - ay);
            auto cost = [&](long double u) { long double fx = cx + u * (dx - cx), fy = cy + u * (dy - cy); return hypotl(ex - ax, ey - ay) / p + hypotl(ex - fx, ey - fy) / r + hypotl(dx - fx, dy - fy) / q; };
            long double low = 0, high = 1; for (int i = 0; i < 100; i++) { long double x = (2 * low + high) / 3, y = (low + 2 * high) / 3; if (cost(x) <= cost(y)) high = y; else low = x; } return cost((low + high) / 2); };
        long double low = 0, high = 1; for (int i = 0; i < 100; i++) { long double x = (2 * low + high) / 3, y = (low + 2 * high) / 3; if (inner(x) <= inner(y)) high = y; else low = x; }
        cout << fixed << setprecision(2) << inner((low + high) / 2);''',
        '按原 SCOI 题及样例，p、q、r 是通常的速度，时间为距离除速度；不要被题面“单位时间每单位距离”的措辞误导。',
        complexity=r'每层迭代 $K=100$ 次，时间 $O(K^2)$，额外空间 $O(1)$。')


if __name__ == '__main__':
    run()
    print('Registered ten reviewed binary and geometric optimization articles.')
