"""Reviewed interval DP, circular choices, conditional knapsacks and merging."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_palindrome_support import MANACHER, EXPLANATION


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(15447, 1900, ['区间动态规划', '前缀和'], '从指定灯开始，沿直线关掉所有路灯，移动期间未关灯都耗电，最小化总能耗。',
        '经过一盏灯时关掉不会花时间，也不会使后续更差，所以已关灯一定是包含起点的连续区间。dp[l][r][0/1]记录已关[l,r]、人站左/右端的最少耗能。继续去l−1或r+1时，移动耗时为距离，耗能等于距离乘“此次出发前所有未关灯的功率和”。区间功率用前缀和计算。起点灯立即关掉，初态区间仅起点且代价0。按区间长度递增，向两侧扩展。',
        r'''int n; while (cin >> n) { int start; cin >> start; start--; vector<long long> position(n), power(n), prefix(n + 1); for (int i = 0; i < n; i++) { cin >> position[i] >> power[i]; prefix[i + 1] = prefix[i] + power[i]; } const long long inf = 1LL << 60; vector<vector<array<long long,2>>> dp(n,vector<array<long long,2>>(n,{inf,inf})); dp[start][start] = {0,0}; for (int length = 1; length <= n; length++) for (int l = max(0,start - length + 1); l <= start && l + length <= n; l++) { int r = l + length - 1; if (r < start) continue; long long remaining = prefix[n] - (prefix[r + 1] - prefix[l]); for (int side = 0; side < 2; side++) if (dp[l][r][side] != inf) { int p = side ? r : l; if (l > 0) dp[l - 1][r][0] = min(dp[l - 1][r][0],dp[l][r][side] + (position[p] - position[l - 1]) * remaining); if (r + 1 < n) dp[l][r + 1][1] = min(dp[l][r + 1][1],dp[l][r][side] + (position[r + 1] - position[p]) * remaining); } } cout << min(dp[0][n - 1][0],dp[0][n - 1][1]) << '\n'; }''',
        '移动到下一盏灯的途中，它仍然亮着，剩余功率要在扩展区间前计算。输入灯已按位置排序，多组读至EOF。', complexity=r'每组时间、空间均为 $O(n^2)$。')
    put(50493, 1800, ['区间动态规划', '环形展开'], '环上只能合并相邻石堆，求全部合并的最小和最大总代价。',
        '复制一遍石堆，把环的断点转成长度n的连续区间。dp[l][r]枚举最后一次合并的分界k，代价是左右子区间代价之和，再加整个[l,r]的石子总数。分别维护最小与最大值，从长度2到n计算。最后在全部n个长度n区间中分别取最小和最大。单堆无需合并，初值0。',
        r'''int n; cin >> n; vector<long long> a(2 * n), prefix(2 * n + 1); for (int i = 0; i < n; i++) { cin >> a[i]; a[i + n] = a[i]; } for (int i = 0; i < 2 * n; i++) prefix[i + 1] = prefix[i] + a[i]; vector<vector<long long>> low(2 * n,vector<long long>(2 * n)), high = low; for (int length = 2; length <= n; length++) for (int l = 0; l + length <= 2 * n; l++) { int r = l + length - 1; low[l][r] = 1LL << 60; high[l][r] = -(1LL << 60); long long sum = prefix[r + 1] - prefix[l]; for (int k = l; k < r; k++) { low[l][r] = min(low[l][r],low[l][k] + low[k + 1][r] + sum); high[l][r] = max(high[l][r],high[l][k] + high[k + 1][r] + sum); } } long long minimum = 1LL << 60, maximum = -(1LL << 60); for (int l = 0; l < n; l++) { minimum = min(minimum,low[l][l + n - 1]); maximum = max(maximum,high[l][l + n - 1]); } cout << minimum << '\n' << maximum;''',
        '合并必须相邻，不能用任取两堆的Huffman贪心。只计算长度至n的区间，并依题目输出先最小、后最大。', complexity=r'时间 $O(n^3)$，空间 $O(n^2)$。')
    put(51170, 1600, ['区间动态规划', '前缀和'], '线性排列的相邻沙堆依次合并，求最小总代价。',
        'dp[l][r]为把连续区间[l,r]合成一堆的最小代价。最后一定由[l,k]、[k+1,r]两堆合并，故枚举k，并加上区间总重量。长度1代价0，其余从短到长计算；前缀和常数时间求最后合并费用。',
        r'''int n; cin >> n; vector<long long> prefix(n + 1); for (int i = 1; i <= n; i++) { long long x; cin >> x; prefix[i] = prefix[i - 1] + x; } vector<vector<long long>> dp(n,vector<long long>(n)); for (int length = 2; length <= n; length++) for (int l = 0; l + length <= n; l++) { int r = l + length - 1; dp[l][r] = 1LL << 60; for (int k = l; k < r; k++) dp[l][r] = min(dp[l][r],dp[l][k] + dp[k + 1][r] + prefix[r + 1] - prefix[l]); } cout << dp[0][n - 1];''',
        '这里是一排，不能复制成环后另选起点。只有两子区间合并完成后，才加一次整个区间总重。', complexity=r'时间 $O(n^3)$，空间 $O(n^2)$。')
    put(207781, 1600, ['贪心', '递推'], '两人一船，每次耗时取较慢者，船必须随人返回，求所有人过河最少总时间。',
        '排序t1≤t2≤…。每次把最慢两人x、y永久送到对岸，有两种标准最优方式：最快两人先过、t1返回、x和y过、t2返回，代价t1+2t2+y；或t1分别带y、x过去并返回两次，代价2t1+x+y。取较小者，剩下问题规模减二。交换论证可把所有承担返回的人替成最快者或次快者，最后运送最慢两人的阶段便落入这两类。余下1人取t1，2人取t2，3人取t1+t2+t3。',
        r'''int n; cin >> n; vector<long long> t(n); for (auto &x : t) cin >> x; sort(t.begin(),t.end()); long long answer = 0; int remaining = n; while (remaining > 3) { answer += min(t[0] + 2 * t[1] + t[remaining - 1],2 * t[0] + t[remaining - 2] + t[remaining - 1]); remaining -= 2; } if (remaining == 3) answer += t[0] + t[1] + t[2]; else if (remaining == 2) answer += t[1]; else if (remaining == 1) answer += t[0]; cout << answer;''',
        '船不能自己回来。最慢两人同船未必最优，必须比较两种搬运策略。总时间用64位。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(23501, 1800, ['Manacher', '环形展开'], '允许把前缀移到末尾，最大化旋转后某个回文子串的长度。',
        '令T=S+S。S任意旋转是T中一个长度n的窗口；反过来，T中任何长度不超过n的连续段，都能放入某个这样的窗口（越过第二份起点的段可整体左移n）。因此只需找T中长度不超过n的最长回文。\n\n' + EXPLANATION + '\n\n奇、偶回文分别把长度截到不超过n的最大同奇偶长度，取最大即可。截短同中心回文仍是回文，故不需要重新验证。',
        r'''string s; cin >> s; int n = s.size(); string doubled = s + s; PalindromeRadii p(doubled); int oddLimit = n % 2 ? n : n - 1, evenLimit = n % 2 ? n - 1 : n, answer = 1; for (int i = 0; i < 2 * n; i++) { answer = max(answer,min(2 * p.odd[i] - 1,oddLimit)); answer = max(answer,min(2 * p.even[i],evenLimit)); } cout << answer;''',
        '不能允许回文超过原串长度。截断奇回文与偶回文时要分别保留奇偶性。', declarations=MANACHER, complexity=r'时间、空间均为 $O(n)$。')
    put(24870, 1800, ['依赖背包', '01背包'], '买游戏必须先买其专属主机，主机和游戏各至多一个，求预算内最大产奶价值。',
        '按主机分组处理。全局dp[c]表示预算c的最优价值。当前组先设temporary[c]=dp[c−主机价格]，表示已经付过当前主机的钱；不足主机价格的状态不可达。再将本组每个游戏在temporary上倒序做01背包。全部游戏处理完后，将temporary与原dp逐预算取最大，表示买本主机或不买。这样主机钱恰付一次，又允许任意游戏子集，避免枚举至多2^10种组合再和全部预算卷积。',
        r'''int n, budget; cin >> n >> budget; const long long neg = -(1LL << 60); vector<long long> dp(budget + 1); while (n--) { int consolePrice, games; cin >> consolePrice >> games; vector<long long> temporary(budget + 1,neg); for (int c = consolePrice; c <= budget; c++) temporary[c] = dp[c - consolePrice]; while (games--) { int price, value; cin >> price >> value; for (int c = budget; c >= price; c--) if (temporary[c - price] != neg) temporary[c] = max(temporary[c],temporary[c - price] + value); } for (int c = 0; c <= budget; c++) dp[c] = max(dp[c],temporary[c]); } cout << dp[budget];''',
        '不能让游戏从全局dp直接转移，否则会不付主机钱。处理一个主机组期间保持原dp不变。', complexity=r'总游戏数 $G\le500$，时间 $O((n+G)V)$，空间 $O(V)$。')
    put(17193, 1800, ['位集', '动态规划'], '每个变量在指定整数区间取值，统计所有平方和的不同取值数。',
        '最大平方和是100*100²=一百万。用位集can的第s位表示和s可达，初始只有0。处理一组[l,r]时，新位集等于所有can向左平移x²位的按位或，x遍历[l,r]，完成后整体替换。每组恰选一个数，因此所有移位必须来自同一个旧位集。最后统计置一位数。',
        r'''int n; cin >> n; constexpr int limit = 1000001; bitset<limit> can, next; can[0] = 1; while (n--) { int l,r; cin >> l >> r; next.reset(); for (int x = l; x <= r; x++) next |= can << (x * x); can = next; } cout << can.count();''',
        '统计不同和值，方案重复不重复增加答案。不能在本组中边移位边写回can，否则会从一个区间选多个数。', complexity=r'值域上界 $S=10^6$，区间总宽度 $R\le10^4$，时间 $O(R\lceil S/w\rceil)$，空间 $O(S)$ 位。')
    put(50500, 1900, ['区间动态规划', '大整数'], '凸多边形三角剖分，最小化各三角形三顶点权值乘积之和。',
        '固定区间端点l、r所连的边，最后与这条边相邻的三角形第三点必为某个k，左右剩余多边形独立。转移dp[l][r]=min(dp[l][k]+dp[k][r]+a[l]*a[k]*a[r])，k严格在l、r之间；少于三个点代价0。N≤50、每权小于十亿，总值小于48*10^27，超过64位但在128位范围内，使用unsigned __int128保存并手动十进制输出。',
        r'''int n; cin >> n; vector<unsigned long long> a(n); for (auto &x : a) cin >> x; using Big = unsigned __int128; vector<vector<Big>> dp(n,vector<Big>(n)); for (int length = 3; length <= n; length++) for (int l = 0; l + length <= n; l++) { int r = l + length - 1; dp[l][r] = ~Big(0); for (int k = l + 1; k < r; k++) dp[l][r] = min(dp[l][r],dp[l][k] + dp[k][r] + Big(a[l]) * a[k] * a[r]); } Big value = dp[0][n - 1]; string result; do { result += char('0' + value % 10); value /= 10; } while (value); reverse(result.begin(),result.end()); cout << result;''',
        '乘法前先转128位，否则中间乘积已溢出。这里分界点k同时属于两子多边形，不能误写成互不共享端点的石子合并转移。', complexity=r'时间 $O(n^3)$，空间 $O(n^2)$。', cases=[{'input':'3\n999999999 999999999 999999999','output':str(999999999**3)}])
    put(24438, 2000, ['动态规划', '区间合并'], '相邻相等值可合成加一的值，最大化最后能生成的某个数字，N至262144。',
        '对目标值v，end[v][l]表示从l开始能完整合成一个v的区间的右开端点，不存在记0。若原a[l]=v，区间就是单点；否则要把两个相邻的v−1拼起来，设mid=end[v−1][l]，再接end[v−1][mid]。\n\n为什么每个起点、目标值只有一个可能端点？把数x看成质量2^x，合并保持总质量；所有初始质量正，固定起点的前缀质量严格递增，所以给定2^v至多对应一个端点。只需上一层end数组，v最多40+log2N≤58，滚动处理并记录有解的最大v。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; vector<int> previous(n + 1), current(n + 1); int answer = 0; for (int value = 1; value <= 58; value++) { fill(current.begin(),current.end(),0); for (int l = n - 1; l >= 0; l--) { if (a[l] == value) current[l] = l + 1; else { int mid = previous[l]; if (mid > 0 && mid < n) current[l] = previous[mid]; } if (current[l]) answer = value; } previous.swap(current); } cout << answer;''',
        '不能总是先合并最左边的一对，样例已经给出反例。右端点用右开下标，n表示恰好用到末尾，不能再接第二段。', complexity=r'时间 $O(58n)$，空间 $O(n)$。')
    put(21467, 1600, ['完全背包', '贪心'], '删减或重建无限货币面额，保留可表示的全部金额，求最少面额数。',
        '先排序面额，从小到大检查。若当前面额x已可由更小保留面额组成，它可以删除，所有使用x的表示都能替换。若不能组成，就必须加入：任意等价系统中用于组成x的面额均≤x，且它们自己也必须能由原系统表示；若不直接用x，只可能来自比x更小的原面额，矛盾。加入新面额后正序做完全背包可达性，更新到最大原面额即可。',
        r'''int tests; cin >> tests; while (tests--) { int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; sort(a.begin(),a.end()); int limit = a.back(), answer = 0; vector<bool> can(limit + 1); can[0] = true; for (int x : a) if (!can[x]) { answer++; for (int s = x; s <= limit; s++) can[s] = can[s] || can[s - x]; } cout << answer << '\n'; }''',
        '每种面额无限张，更新要正序。重复面额会自然被可达性去掉，不会重复计数。', complexity=r'每组时间 $O(n\log n+nA)$，空间 $O(A)$，$A\le25000$。')
    put(19990, 1200, ['动态规划', '可达性'], '每首歌前必须按指定幅度调高或调低，过程不越界，求最后最大音量。',
        '用布尔数组记录当前所有可达音量。初始只有begin。每个变化c从旧音量v分别转移到v−c、v+c，越界的不加入。用新数组替换，全部歌曲结束后从最大音量向下找首个可达者，没有则−1。',
        r'''int n, begin, limit; cin >> n >> begin >> limit; vector<bool> can(limit + 1); can[begin] = true; while (n--) { int change; cin >> change; vector<bool> next(limit + 1); for (int v = 0; v <= limit; v++) if (can[v]) { if (v >= change) next[v - change] = true; if (v + change <= limit) next[v + change] = true; } can.swap(next); } int answer = -1; for (int v = limit; v >= 0; v--) if (can[v]) { answer = v; break; } cout << answer;''',
        '每次必须调整，不能保留原音量作为“不操作”。更新必须基于上一首歌状态。', complexity=r'时间 $O(nM)$，空间 $O(M)$。')
    put(19909, 1700, ['区间动态规划', '覆盖'], '一次可把任意连续段刷成同色，后刷覆盖前刷，求达到目标的最少次数。',
        'dp[l][r]为从空白刷出目标区间的最少次数。先考虑单独刷l，代价1+dp[l+1][r]。若某个k>l与l同色，可让刷到k的那一笔同时覆盖l，再单独修复中间[l+1,k−1]，代价dp[l+1][k−1]+dp[k][r]。枚举所有同色k取最小，空区间代价0，按长度递增计算。这样的合并对应最优方案中最后留下l颜色的那笔所覆盖的后续同色位置。',
        r'''string s; cin >> s; int n = s.size(); vector<vector<int>> dp(n,vector<int>(n)); for (int l = n - 1; l >= 0; l--) { dp[l][l] = 1; for (int r = l + 1; r < n; r++) { dp[l][r] = 1 + dp[l + 1][r]; for (int k = l + 1; k <= r; k++) if (s[k] == s[l]) dp[l][r] = min(dp[l][r],(k == l + 1 ? 0 : dp[l + 1][k - 1]) + dp[k][r]); } } cout << dp[0][n - 1];''',
        '颜色可以覆盖，不能只统计相邻色块数。刷同色两端时，中间可以先被一起刷后再重刷。', complexity=r'时间 $O(n^3)$，空间 $O(n^2)$。')
    put(24949, 1700, ['动态规划', '区间选择'], '跑一分钟疲劳加一，停下后必须休息到零才能再跑，结束时疲劳零，最大化跑步距离。',
        '把一次完整活动看成“连续跑k分钟，再连续休息k分钟”，1≤k≤M；块开始和结束疲劳都为0。dp[t]表示前t分钟已回到疲劳0的最大距离。可以再休息一分钟继承dp[t−1]；也可用一个长度2k的完整块结束在t，此块跑的是t−2k+1到t−k，距离用前缀和求，转自dp[t−2k]。所有合法计划都可按归零时刻拆成这些块，故没有漏解。',
        r'''int n, m; cin >> n >> m; vector<long long> prefix(n + 1), dp(n + 1); for (int i = 1; i <= n; i++) { int x; cin >> x; prefix[i] = prefix[i - 1] + x; } for (int t = 1; t <= n; t++) { dp[t] = dp[t - 1]; for (int run = 1; run <= m && 2 * run <= t; run++) dp[t] = max(dp[t],dp[t - 2 * run] + prefix[t - run] - prefix[t - 2 * run]); } cout << dp[n];''',
        '休息中途不能恢复跑步。末尾剩余疲劳不合法，所以只维护完整归零块，不取所有疲劳状态的最大值。', complexity=r'时间 $O(nM)$，空间 $O(n)$。')
    put(25147, 1300, ['动态规划', '网格'], '从左上走到右下，每步必须到下一列，行号变动至多1，最大化经过的金币和。',
        '按列推进。dp[r]为上一列停在r行的最大金币和，下一列r可由上一列r−1、r、r+1转移。初始仅左上格可达，其他为负无穷，最后必须取右下而非末列任意行。',
        r'''int rows, cols; cin >> rows >> cols; vector<vector<int>> a(rows,vector<int>(cols)); for (auto &row : a) for (int &x : row) cin >> x; const int neg = -1000000000; vector<int> dp(rows,neg), next(rows); dp[0] = a[0][0]; for (int c = 1; c < cols; c++) { fill(next.begin(),next.end(),neg); for (int r = 0; r < rows; r++) for (int previous = max(0,r - 1); previous <= min(rows - 1,r + 1); previous++) if (dp[previous] != neg) next[r] = max(next[r],dp[previous] + a[r][c]); dp.swap(next); } cout << dp[rows - 1];''',
        '每次列号加一，不能在同一列上下移动。起点只有(1,1)，不能把第一列全部初始化为对应金币。', complexity=r'时间 $O(RC)$，存输入 $O(RC)$、额外DP空间 $O(R)$。')
    put(25148, 1400, ['最长上升子序列', '二分'], '从队列中保持顺序挑出严格递增的编号，求最多数量。',
        'tails[len−1]记录长度len的严格上升子序列的最小末尾。扫描编号x，找到第一个≥x的位置并替换；若不存在就追加。更小末尾使未来更容易接上，而不会改变已有长度的可行性，故最终数组长度即LIS长度。编号可能使用完整32位无符号范围，用64位读取。',
        r'''int n; cin >> n; vector<long long> tails; while (n--) { long long x; cin >> x; auto it = lower_bound(tails.begin(),tails.end(),x); if (it == tails.end()) tails.push_back(x); else *it = x; } cout << tails.size();''',
        '要求严格递增，用lower_bound而非upper_bound；相同编号不会增加长度。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(210520, 1800, ['01背包', '生成函数', '逆向递推'], '分别禁用每件物品，输出其他物品恰好装满每个容量的方案数个位。',
        '先做全部物品的01计数背包f，取模10。禁用一件重量w后的方案数记g；按是否选该件物品分解，有f[j]=g[j]+g[j−w]。因此g[j]=f[j]−g[j−w]，从小到大递推，j<w时g[j]=f[j]。每件物品只需线性扫一遍容量，不必重做n次背包。重量相同的物品仍按不同编号区分，这个分解禁用的正是当前这一件。',
        r'''int n, m; while (cin >> n >> m) { vector<int> weight(n), all(m + 1); for (int &x : weight) cin >> x; all[0] = 1; for (int w : weight) for (int j = m; j >= w; j--) all[j] = (all[j] + all[j - w]) % 10; for (int w : weight) { vector<int> without(m + 1); without[0] = 1; for (int j = 1; j <= m; j++) { without[j] = (all[j] - (j >= w ? without[j - w] : 0) + 10) % 10; cout << without[j]; } cout << '\n'; } }''',
        '求g时正序，建全体f时倒序，两种方向不同。每行各个位直接拼接，无空格。减法加10后取模。', complexity=r'每组时间 $O(nm)$，空间 $O(n+m)$。')
    put(227595, 1800, ['区间动态规划', '环形展开'], '环上每次选择左右最近的未访问格，按访问顺序乘递增权重，求最大分数。',
        '已访问格构成环上一段，所以未访问部分也是连续区间，每步只能取其两端。复制数组后，对所有长度至n的区间做“剩余区间DP”。剩余len格时，这一步系数为n−len+1，选择左端或右端后剩余长度减一。按长度递增可滚动为一维，左端l从小到大更新。最后对所有长度n窗口取最大，相当于任选开始位置。首步选择原环任意点，都可在某个窗口中作为端点出现。',
        r'''int n; cin >> n; vector<long long> a(2 * n), dp(2 * n + 1); for (int i = 0; i < n; i++) { cin >> a[i]; a[i + n] = a[i]; } for (int length = 1; length <= n; length++) for (int l = 0; l + length <= 2 * n; l++) { int r = l + length - 1; long long coefficient = n - length + 1; dp[l] = max(a[l] * coefficient + dp[l + 1],a[r] * coefficient + dp[l]); } cout << *max_element(dp.begin(),dp.begin() + n);''',
        '跳过已访问格去找最近未访问格，不是每次只能移动到物理相邻的一格。总分用64位；滚动更新左端从小到大。', complexity=r'时间 $O(n^2)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
