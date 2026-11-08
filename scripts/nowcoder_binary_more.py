"""Reviewed binary predicates with exact count and arithmetic boundaries."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(285706, 1900, ['二分答案', '01 分数规划', '快速选择'], '恰好选 k 件，最大化总价值除以总体积。',
        '对于候选比值 x，要求 sum(v)/sum(w)>=x，等价于 sum(v-xw)>=0。给每件物品打分 v-xw，选得分最大的 k 件就是该 x 下的最优选择。若这 k 项之和非负，x 可行，否则不可行。可行性随 x 增大而减弱，二分零到最大的单件价值体积比。每轮用 nth_element 选出前 k 大，不必完整排序。',
        r'''int n, k; cin >> n >> k; vector<long double> weight(n), value(n), score(n); long double low = 0, high = 0; for (int i = 0; i < n; i++) { cin >> weight[i] >> value[i]; high = max(high, value[i] / weight[i]); }
        for (int iteration = 0; iteration < 65; iteration++) { long double mid = (low + high) / 2; for (int i = 0; i < n; i++) score[i] = value[i] - mid * weight[i];
            if (k < n) nth_element(score.begin(), score.begin() + k, score.end(), greater<long double>()); long double sum = accumulate(score.begin(), score.begin() + k, 0.0L); if (sum >= 0) low = mid; else high = mid; }
        cout << fixed << setprecision(12) << low;''',
        '必须比较总价值除总体积，按单件比值直接选前 k 个通常错误。k=n 时无需调用分割迭代器在末尾的 nth_element。',
        complexity=r'每轮快速选择平均 $O(n)$，固定迭代 $K=65$ 次，平均总时间 $O(Kn)$，空间 $O(n)$。', floating_output=True)
    if 'nowcoder-global::24866' not in existing:
        reviewed_clone(24866, 287777, '完整核对USACO Music Notes，同样零时刻开始、音符右端不包含、N/Q五万与单拍一万；分行差异不影响空白读取。')
    put(14733, 1100, ['二分查找', '整数运算'], '多次统计闭非负整数区间中的完全平方数，零也算平方。',
        '定义 count(x) 为零到 x 中的平方数个数。x<0 时为零，否则平方根的整数取值为零到 floor(sqrt(x))，所以 count(x)=floor(sqrt(x))+1。查询答案为 count(r)-count(l-1)。用整数二分找最大的根，平方在 long long 中计算，避免浮点临界误差。',
        r'''auto count = [](long long x) { if (x < 0) return 0LL; long long low = 0, high = 100000; while (low < high) { long long mid = (low + high + 1) / 2; if (mid * mid <= x) low = mid; else high = mid - 1; } return low + 1; };
        int q; cin >> q; while (q--) { long long l, r; cin >> l >> r; cout << count(r) - count(l - 1) << '\n'; }''',
        '零的平方根为零，[0,0] 应得到一。l=0 时，辅助函数应支持 -1。',
        complexity=r'每次查询时间 $O(\log r)$，额外空间 $O(1)$。',
        cases=[{'input': '3\n0 0\n0 1\n999950884 999950884', 'output': '1\n2\n1'}])
    put(16462, 1600, ['二分答案', '贪心'], '至多移走 M 块中间岩石，最大化保留石头相邻距离的最小值。',
        '二分最小跳距 d，从起点贪心保留最早能距上一块至少 d 的岩石；若距离不足就移走当前石头。保留位置越靠前，越有利于后续选石，所以这样使用最少移除数。把终点也放进扫描：若最后一跳不足，计一次移除可理解为移除之前最后保留的中间石头；此前两跳合并后足够长。移除数不超过 M 则 d 可行。',
        r'''long long length; int n, m; cin >> length >> n >> m; vector<long long> positions(n + 1); for (int i = 0; i < n; i++) cin >> positions[i]; positions[n] = length;
        auto possible = [&](long long distance) { int removed = 0; long long previous = 0; for (long long x : positions) { if (x - previous < distance) removed++; else previous = x; } return removed <= m; };
        long long low = 1, high = length; while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low;''',
        '起终点不能真的删除，末跳不足的计数必须按删除前一中间石头理解。没有中间石头时答案就是 L。',
        complexity=r'时间 $O(n\log L)$，空间 $O(n)$。',
        cases=[{'input': '10 0 0', 'output': '10'}, {'input': '10 1 1\n9', 'output': '10'}])
    put(24083, 2200, ['二分答案', '贪心', '前缀计数'], '队首牛领取礼物后按固定插队数归队，求永远拿不到礼物的牛数。',
        '未拿过礼物的牛之间不能互相越过，因此能拿到的牛是原队列的一个前缀。令 d[i]=N-c[i]，表示领取后插回的一基位置。判断前 x 头是否已能形成永久阻塞：统计这 x 个 d 中，是否存在 j 使 d<=j 的牛至少有 j 头。若存在，这 j 头总能挡在后续未领取者前面：队首拿完后仍插在前 j 位，不会跑到目标牛后方。反之，第一头永远无法领取的牛最终会稳定在某个正位置 j，其前方的 j 头领取后都不越过它，所以恰有至少 j 个 d<=j。该条件充分且必要。\n\n对前 x 头按 d 做频次数组，再扫前缀计数检查条件。它随 x 增加只会从假变真。二分第一个满足条件的 x，前 x 头都至少领取一次，之后 N-x 头永远不能领取。x=N 时总能满足，统一涵盖所有牛都拿得到的情况。',
        r'''int n; cin >> n; vector<int> position(n), frequency(n + 1); for (int &x : position) { cin >> x; x = n - x; }
        auto blocks = [&](int count) { fill(frequency.begin(), frequency.end(), 0); for (int i = 0; i < count; i++) frequency[position[i]]++; int prefix = 0;
            for (int j = 1; j <= n; j++) { prefix += frequency[j]; if (prefix >= j) return true; } return false; };
        int low = 1, high = n; while (low < high) { int mid = (low + high) / 2; if (blocks(mid)) high = mid; else low = mid + 1; } cout << n - low;''',
        '插回位置是 N-c[i]，不要混同为原始插队数。无限过程不能靠给一个任意模拟步数来断言永远领不到。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。',
        cases=[{'input': '3\n0 0 0', 'output': '0'}, {'input': '3\n0 2 2', 'output': '1'}])
    put(23049, 1400, ['二分答案'], '把已有木棍裁成至少 K 段等长整数木棍，求最大段长，无法得到正长度则为零。',
        '给定正长度 d，每根原木能贡献 floor(L[i]/d) 段。总段数至少 K 就可行，目标 d 越大段数越少。二分最大可行正长度，以零为已知可行的哨兵；判定从不除以零。累计达到 K 后即可提前返回。',
        r'''int n; long long k; cin >> n >> k; vector<long long> a(n); long long high = 0; for (auto &x : a) { cin >> x; high = max(high, x); }
        auto possible = [&](long long length) { long long count = 0; for (long long x : a) { count += x / length; if (count >= k) return true; } return false; };
        long long low = 0; while (low < high) { long long mid = low + (high - low + 1) / 2; if (possible(mid)) low = mid; else high = mid - 1; } cout << low;''',
        '允许丢掉剩余段，也允许多切出 K 段后只使用 K 段，因此判定是至少 K。若总原长都不足 K，输出零。',
        complexity=r'时间 $O(n\log L_{max})$，空间 $O(n)$。')
    if 'nowcoder-global::14301' not in existing:
        reviewed_clone(14301, 287787, '两份原题面现已统一为HDU6231同源版本：T<=10、n<=10^5、k与m条件、输出第m大及全部样例逐条相同。')
    put(16597, 1800, ['二分答案', '前缀和'], '选重量阈值，让所有区间内的数量乘价值和之和，最接近标准 S。',
        '阈值 W 增大时，选中的矿石只会减少，每个区间数量与价值和均不增，所以总检验值 Y 单调不增。固定 W，预处理符合阈值矿石的计数前缀与价值前缀，每个区间 O(1) 求数量乘价值和。二分第一个 Y<=S 的阈值，只需比较这个阈值与前一个阈值，分别给出跨越 S 两侧的最近候选。W=maxWeight+1 会选不到任何矿石，保证二分有界。',
        r'''int n, m; long long standard; cin >> n >> m >> standard; vector<int> weight(n + 1), value(n + 1); int maxWeight = 0; for (int i = 1; i <= n; i++) { cin >> weight[i] >> value[i]; maxWeight = max(maxWeight, weight[i]); }
        vector<pair<int,int>> intervals(m); for (auto &[l, r] : intervals) cin >> l >> r; vector<long long> count(n + 1), sum(n + 1);
        auto evaluate = [&](int threshold) { for (int i = 1; i <= n; i++) { bool chosen = weight[i] >= threshold; count[i] = count[i - 1] + chosen; sum[i] = sum[i - 1] + (chosen ? value[i] : 0); }
            __int128 result = 0; for (auto [l, r] : intervals) result += (__int128)(count[r] - count[l - 1]) * (sum[r] - sum[l - 1]); return result; };
        int low = 1, high = maxWeight + 1; while (low < high) { int mid = (low + high) / 2; if (evaluate(mid) <= standard) high = mid; else low = mid + 1; }
        long long answer = standard; for (int threshold : {low, low - 1}) if (threshold >= 1) { __int128 result = evaluate(threshold), difference = result >= standard ? result - standard : standard - result; if (difference < answer) answer = (long long)difference; } cout << answer;''',
        '总检验值按题面完整范围可超过 64 位，累加使用 __int128。最终最小差不超过 S，因为可选择空集；因此答案可安全用 long long。',
        complexity=r'时间 $O((n+m)\log W_{max})$，空间 $O(n+m)$。')
    put(14380, 1900, ['排序', '双指针', '计数'], '对原下标 i<j，累计 a[i]+a[j] 的十进制位数减 a[i] 位数，零按一位算。',
        '一个非负整数的位数等于一，加上它达到的阈值 10、100、1000……的数量。因此先把所有数对各自的一贡献记入，再减去原下标权重 (n-1-i)*digits(a[i])。剩下只需对每个十进制阈值 T，统计有多少无序数对满足 a[i]+a[j]>=T；这一部分与原顺序无关，可以排序后双指针。若最小与最大之和已达到 T，就有 right-left 对以最大值为右端的数对达标，然后右端减一；否则左端加一。',
        r'''int n; cin >> n; vector<long long> a(n); long long answer = 0; for (int i = 0; i < n; i++) { cin >> a[i]; int digits = 1; for (long long x = a[i]; x >= 10; x /= 10) digits++; answer += (n - 1LL - i) * (1 - digits); } sort(a.begin(), a.end());
        for (long long threshold = 10; threshold <= 200000000; threshold *= 10) { int left = 0, right = n - 1; while (left < right) { if (a[left] + a[right] >= threshold) { answer += right - left; right--; } else left++; } } cout << answer;''',
        'h(a,b) 对 a、b 不对称，减去 a[i] 位数的那部分必须在排序前按原下标算。h(0,100)=2，h(100,0)=0。',
        complexity=r'时间 $O(n\log n+n\log A)$，空间 $O(n)$；本题最多八个十进制阈值。',
        cases=[{'input': '2\n0 100', 'output': '2'}, {'input': '2\n100 0', 'output': '0'}])


if __name__ == '__main__':
    run()
    print('Registered nine reviewed binary and counting articles.')
