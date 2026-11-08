"""Linear states, exact probabilities and ordinary/dependent knapsacks."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    if 'nowcoder-global::20650' not in existing:
        reviewed_clone(20650, 50038, '将n个孤立点合并成树，每次连接不同连通块，代价为块大小差；与已验证的单元素堆合并模型完全等价。多组、n至一万亿由64位记忆化递推覆盖。',
                       replacements={'从 n 堆各一颗糖出发，两堆合并代价为大小差，求总成本最小值。':'从n个孤立点出发，连接两块的代价为块大小差，求连成树的最小总代价。',
                                     '两子堆相等':'两个子连通块相等', '所有子堆的 G':'所有子连通块的 G', '初始 G[1]':'单点初始 G[1]'})
    put(20875, 1200, ['动态规划', '计数'], '每天三种外卖，不能连续三天相同，统计n天方案数模十亿加七。',
        '按末尾相同店铺连续出现1天或2天分两类，数量记one、two。换店时有另外两家可选，所以新one=2*(one+two)；继续同店只允许原来连续1天，所以新two=one。第一天为one=3、two=0，预处理全部十万天后直接回答。',
        r'''const long long mod = 1000000007; const int limit = 100000; vector<long long> answer(limit + 1); long long one = 3, two = 0; answer[1] = 3; for (int n = 2; n <= limit; n++) { long long nextOne = 2 * (one + two) % mod; two = one; one = nextOne; answer[n] = (one + two) % mod; } int tests; cin >> tests; while (tests--) { int n; cin >> n; cout << answer[n] << '\n'; }''',
        '更新two前先保存新one，否则会读到本轮值。连续两天相同仍合法。', complexity=r'预处理时间、空间 $O(10^5)$，每次询问 $O(1)$。')
    put(51216, 1700, ['动态规划', '路径恢复', '字典序'], '按花束顺序选不同花瓶，最大化可为负的美观总值，同值时位置序列字典序最小。',
        '用后缀DP：dp[i][j]表示花i到末尾只能使用花瓶j到末尾的最优值。可跳过瓶j，或把花i放入j并转到dp[i+1][j+1]。没有剩余花时值为0，有花而无瓶时不可达，用负无穷。恢复时从左向右为每束花找最早的j，使本次美观值加剩余最优值仍等于当前最优值，立即选择。这样每一位都尽量靠前，保证全局字典序最小。',
        r'''int f, v; cin >> f >> v; vector<vector<long long>> value(f,vector<long long>(v)); for (auto &row : value) for (auto &x : row) cin >> x; const long long neg = -(1LL << 60); vector<vector<long long>> dp(f + 1,vector<long long>(v + 1,neg)); fill(dp[f].begin(),dp[f].end(),0); for (int i = f - 1; i >= 0; i--) for (int j = v - 1; j >= 0; j--) { dp[i][j] = dp[i][j + 1]; if (dp[i + 1][j + 1] != neg) dp[i][j] = max(dp[i][j],value[i][j] + dp[i + 1][j + 1]); } cout << dp[0][0] << '\n'; int start = 0; long long remaining = dp[0][0]; for (int i = 0; i < f; i++) for (int j = start; j < v; j++) if (dp[i + 1][j + 1] != neg && value[i][j] + dp[i + 1][j + 1] == remaining) { cout << j + 1 << (i + 1 == f ? '\n' : ' '); remaining -= value[i][j]; start = j + 1; break; }''',
        '负数美观值也必须放完所有花，不能用全0初始化不可达状态。普通正向回溯随意处理平局可能不满足字典序。', complexity=r'时间、空间均为 $O(FV)$。', cases=[{'input':'2 3\n0 0 0\n0 0 0','output':'0\n1 2'}])
    put(16850, 1800, ['动态规划', '路径恢复'], '玩家每秒左右最多两格，只能在整秒末接到落下的馅饼，最大化得分并输出每秒移动。',
        '馅饼初始在高度H的格子，玩家所在底格高度1，下降距离为H−1。只有(H−1)能被速度整除时，馅饼才在整秒恰好落入玩家格，接取时刻为初始时刻+(H−1)/速度。将同一时刻同一位置的分数相加。\n\n设dp[t][x]为t秒末站在x的最大得分，从上一秒x−2到x+2的五个位置转移，再加当前馅饼分数。初始只有正中央可达，时刻0的该处馅饼也计分。记录每个状态的前驱位置，所有时刻中取得最高分的最早状态即为结束位置，逆向恢复逐秒移动；选最早时刻可避免收完最后一块后多输出动作。',
        r'''int w, h; cin >> w >> h; vector<tuple<int,int,int>> pies; int startTime, x, speed, score, endTime = 0; while (cin >> startTime >> x >> speed >> score) if ((h - 1) % speed == 0) { int t = startTime + (h - 1) / speed; pies.push_back({t,x,score}); endTime = max(endTime,t); } vector<vector<long long>> reward(endTime + 1,vector<long long>(w + 1)); for (auto [t,p,s] : pies) reward[t][p] += s; const long long neg = -(1LL << 60); vector<vector<long long>> dp(endTime + 1,vector<long long>(w + 1,neg)); vector<vector<int>> parent(endTime + 1,vector<int>(w + 1,-1)); int center = (w + 1) / 2; dp[0][center] = reward[0][center]; long long best = dp[0][center]; int bestTime = 0, bestPosition = center;
        for (int t = 1; t <= endTime; t++) for (int p = 1; p <= w; p++) { for (int previous = max(1,p - 2); previous <= min(w,p + 2); previous++) if (dp[t - 1][previous] != neg && dp[t - 1][previous] + reward[t][p] > dp[t][p]) { dp[t][p] = dp[t - 1][previous] + reward[t][p]; parent[t][p] = previous; } if (dp[t][p] > best) { best = dp[t][p]; bestTime = t; bestPosition = p; } } vector<int> moves; for (int t = bestTime, p = bestPosition; t > 0; t--) { int previous = parent[t][p]; moves.push_back(p - previous); p = previous; } reverse(moves.begin(),moves.end()); cout << best << '\n'; for (int step : moves) cout << step << '\n';''',
        '下降距离是H−1，不能将到达时刻向下或向上取整。不同合法最优移动串均可，校验会模拟每个动作和得分。', complexity=r'最后可接时刻 $T\le1099$，馅饼数 $P$，时间 $O(P+5TW)$，空间 $O(TW+P)$。', checker='falling-pie-walk')
    put(16856, 1700, ['概率动态规划', '整数运算'], '三角钉板中部分钉子被拔掉，求小球落入指定槽的精确既约分数。',
        '以2^n为共同分母，把概率表示为整数份数，顶点初始有2^n份。有钉子时各一半落到下一行的左、右结点；钉子被拔时，球竖直经过下一行两钉之间，直接落到下下行中间结点，全部份数传过去。最多碰n次钉子，所以整数份数每次除二都是精确的。最后取槽位的份数，与2^n求最大公约数约分。',
        r'''int n, target; cin >> n >> target; vector<vector<char>> peg(n); for (int i = 0; i < n; i++) { peg[i].resize(i + 1); for (char &c : peg[i]) cin >> c; } vector<vector<long long>> ways(n + 2,vector<long long>(n + 2)); long long denominator = 1LL << n; ways[0][0] = denominator; for (int i = 0; i < n; i++) for (int j = 0; j <= i; j++) { if (peg[i][j] == '*') { ways[i + 1][j] += ways[i][j] / 2; ways[i + 1][j + 1] += ways[i][j] / 2; } else ways[i + 2][j + 1] += ways[i][j]; } long long numerator = ways[n][target], divisor = gcd(numerator,denominator); cout << numerator / divisor << '/' << denominator / divisor;''',
        '拔掉钉子是跳两行，不是向下一行传给某一边。读取字符会自动跳过任意空白，最后一行保证有钉子。', complexity=r'时间、空间均为 $O(n^2)$。')
    put(16708, 1200, ['网格动态规划', '计数'], '卒只能向下或向右，避开马自身和八个攻击点，统计到目标的路径。',
        '先标记马自身及八种日字跳的位置，只保留棋盘内点。dp[x][y]为到该点的路径数：禁点为0，其余由左和上相加。原点若未被控制，初始化为1。逐行逐列递增处理，依赖都已求出。',
        r'''int n, m, x, y; cin >> n >> m >> x >> y; vector<vector<bool>> blocked(n + 1,vector<bool>(m + 1)); int dx[] = {0,1,1,-1,-1,2,2,-2,-2}, dy[] = {0,2,-2,2,-2,1,-1,1,-1}; for (int k = 0; k < 9; k++) { int a = x + dx[k], b = y + dy[k]; if (a >= 0 && a <= n && b >= 0 && b <= m) blocked[a][b] = true; } vector<vector<long long>> dp(n + 1,vector<long long>(m + 1)); if (!blocked[0][0]) dp[0][0] = 1; for (int i = 0; i <= n; i++) for (int j = 0; j <= m; j++) if (!blocked[i][j] && (i || j)) { if (i) dp[i][j] += dp[i - 1][j]; if (j) dp[i][j] += dp[i][j - 1]; } cout << dp[n][m];''',
        '棋盘包含坐标0，大小应开到n+1、m+1。路径数超过32位，用64位。', complexity=r'时间、空间均为 $O(nm)$。')
    put(16619, 1200, ['动态规划', '计数'], '圆圈里每次传给左或右邻居，恰传m次回到起点的方案数。',
        'dp[t][p]表示传t次后在p的方案数，每一步从左右邻居的上一步方案相加。初始dp[0][0]=1。位置用模n处理，两数组滚动，做满m轮后输出起点。n至少3，左右邻居不同。',
        r'''int n, m; cin >> n >> m; vector<long long> dp(n), next(n); dp[0] = 1; for (int t = 0; t < m; t++) { for (int p = 0; p < n; p++) next[p] = dp[(p + n - 1) % n] + dp[(p + 1) % n]; dp.swap(next); } cout << dp[0];''',
        '每轮从上一轮同时转移，不可直接原地更新。恰好传m次，不能把提前回到起点的方案单独累加。', complexity=r'时间 $O(nm)$，空间 $O(n)$。')
    put(53675, 1300, ['网格动态规划', '滚动数组'], '从左下走到右上，只能向上或向右，避开树，方案数模2333。',
        '反过来从右上向左下走，允许向下或向左，路径一一对应。这样可以按输入从上到下逐行处理，并在每行从右往左更新。dp[c]原来是上一行同列的方案，加上当前行右侧dp[c+1]；遇树则清零。首行右上角的起点单独初始化为1。只需保留一行，不存九百万格地图。',
        r'''int rows, cols; cin >> rows >> cols; vector<int> dp(cols + 1), blocked(cols); for (int r = 0; r < rows; r++) { for (int &x : blocked) cin >> x; for (int c = cols - 1; c >= 0; c--) { if (blocked[c]) dp[c] = 0; else if (r == 0 && c == cols - 1) dp[c] = 1; else dp[c] = (dp[c] + dp[c + 1]) % 2333; } } cout << dp[0];''',
        '原题起点在左下，按左上起点普通转移会算错。反向路径允许流式读取，仍需每行先读完才能倒序更新。', complexity=r'时间 $O(mn)$，额外空间 $O(n)$。')
    put(16664, 1400, ['最长上升子序列', '动态规划'], '删除最少同学，使剩余身高先严格上升再严格下降。',
        '每个位置i分别求以它结尾的严格上升子序列长度left[i]，以及以它开头的严格下降长度right[i]。二者拼接，以i为唯一最高点，总长left[i]+right[i]−1。枚举最高点取最大保留人数，答案为n减去该值。允许最高点在端点，一侧长度为1。',
        r'''int n; cin >> n; vector<int> a(n), left(n,1), right(n,1); for (int &x : a) cin >> x; for (int i = 0; i < n; i++) for (int j = 0; j < i; j++) if (a[j] < a[i]) left[i] = max(left[i],left[j] + 1); for (int i = n - 1; i >= 0; i--) for (int j = i + 1; j < n; j++) if (a[j] < a[i]) right[i] = max(right[i],right[j] + 1); int keep = 0; for (int i = 0; i < n; i++) keep = max(keep,left[i] + right[i] - 1); cout << n - keep;''',
        '相同身高不能出现在严格单调的一侧，比较必须用小于。峰顶在两边计了两次，需要减一。', complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(23413, 1500, ['概率动态规划', '计数'], '买n张三元彩票，奖金均匀为1到4元，求总奖金至少3n的精确概率。',
        '所有4^n种奖金序列等可能。dp[sum]记录已经买若干张后，奖金总和为sum的序列数，每张依次加1、2、3、4。最后把sum≥3n的计数相加作为分子，分母为4^n，用gcd约分。n≤30，4^30=2^60在64位范围内，无需浮点或大整数。n=0的空序列不亏，概率1/1。',
        r'''int n; cin >> n; vector<long long> dp(4 * n + 1); dp[0] = 1; long long denominator = 1; for (int i = 0; i < n; i++) { vector<long long> next(4 * n + 1); for (int sum = 0; sum <= 4 * i; sum++) for (int reward = 1; reward <= 4; reward++) next[sum + reward] += dp[sum]; dp.swap(next); denominator *= 4; } long long numerator = 0; for (int sum = 3 * n; sum <= 4 * n; sum++) numerator += dp[sum]; long long divisor = gcd(numerator,denominator); cout << numerator / divisor << '/' << denominator / divisor;''',
        '不亏包括刚好收回3n。每张只能选四种奖金之一，不能把奖金总额视为等概率。', complexity=r'时间 $O(n^2)$，空间 $O(n)$。', cases=[{'input':'0','output':'1/1'}])
    put(14526, 1700, ['动态规划', '分组背包'], '每天有不同价格的糖果，每天买k个另付k²，确保每天吃一个，求最少花费。',
        '同一天买k个一定取当天最便宜的k个，排序后用前缀和给出商品费用。dp[j]表示前面若干天一共买j个的最小费用。第d天枚举买k个，费用加当天前k个之和及k²，只允许新累计数量j+k≥d，保证此前每日都有糖吃。所有价格和附加费为正，最终只需恰买n个，多买不会更省；故累计数量只开0到n。每一天用新数组，避免重复使用当天糖果。',
        r'''int n, m; cin >> n >> m; const long long inf = 1LL << 60; vector<long long> dp(n + 1,inf); dp[0] = 0; for (int day = 1; day <= n; day++) { vector<long long> price(m), prefix(m + 1); for (auto &x : price) cin >> x; sort(price.begin(),price.end()); for (int k = 1; k <= m; k++) prefix[k] = prefix[k - 1] + price[k - 1]; vector<long long> next(n + 1,inf); for (int previous = 0; previous <= n; previous++) if (dp[previous] != inf) for (int buy = 0; buy <= m && previous + buy <= n; buy++) if (previous + buy >= day) next[previous + buy] = min(next[previous + buy],dp[previous] + prefix[buy] + 1LL * buy * buy); dp.swap(next); } cout << dp[n];''',
        '允许提前买来囤着，但不能使用未来糖果；累计买入量必须在每个日期都不低于日期。附加费按当天总购买数平方，只收一次。', complexity=r'时间 $O(nm\log m+n^2m)$，空间 $O(n+m)$。')
    put(207751, 1700, ['动态规划', '滚动数组'], '恰选m个物品，任意两位置距离至少k，受欢迎度可为负，最大化总和。',
        '设dp[j][i]为前i个位置恰选j个的最优值。不选i转自dp[j][i−1]，选i转自dp[j−1][max(0,i−k)]+a[i]。j=0时所有前缀值为0，其他不可达状态设负无穷，避免负值物品被错误跳过。按j分层，仅保留上一层和本层数组。不同物品位置必须不同，故实现将间隔至少设为1。',
        r'''int n, m, k; cin >> n >> m >> k; k = max(k,1); vector<long long> a(n + 1); for (int i = 1; i <= n; i++) cin >> a[i]; const long long neg = -(1LL << 60); vector<long long> previous(n + 1,0), current(n + 1); for (int count = 1; count <= m; count++) { fill(current.begin(),current.end(),neg); for (int i = 1; i <= n; i++) { current[i] = current[i - 1]; long long before = previous[max(0,i - k)]; if (before != neg) current[i] = max(current[i],before + a[i]); } previous.swap(current); } cout << previous[n];''',
        '要求恰好m个，不能把负收益都不选。选择i后，前一个可选位置最多是i−k，包括等号。', complexity=r'时间 $O(nm)$，空间 $O(n)$。')
    put(17871, 1200, ['01背包', '子集和'], '苹果不可切开，分两堆尽量等重，重的一堆给tokitsukaze。',
        '总重量为S，较轻堆重量不超过S/2。用01背包求可达到且不超过S/2的最大重量x，另外一堆就是S−x，差值随x增大而减小。每个苹果倒序更新可达重量，保证只取一次。',
        r'''int n; cin >> n; vector<int> a(n); int sum = 0; for (int &x : a) { cin >> x; sum += x; } int capacity = sum / 2; vector<bool> can(capacity + 1); can[0] = true; for (int x : a) for (int s = capacity; s >= x; s--) can[s] = can[s] || can[s - x]; int x = capacity; while (!can[x]) x--; cout << x << ' ' << sum - x;''',
        '输出先轻后重，不要求两个人的苹果个数相同。容量倒序，不能把同一苹果重复使用。', complexity=r'时间 $O(nS)$，空间 $O(S)$，$S\le10000$。')
    put(19158, 1800, ['动态规划', '差值背包'], '每次可拿走天平两侧差不超过m的武器，允许多次操作，最大化带走总重量。',
        '多次操作不比一次更强：每组的重量差绝对值≤m，把下一组较重侧朝向目前较轻侧合并，总差变成两个差的绝对值，仍≤m。因此可把所有拿走的武器放在一次称量中。\n\n用dp[d]记录当前左右重量差绝对值为d时，能选出的最大总重。每件武器有不选、放较重侧、放较轻侧三种选择，差分别为d、d+x、|d−x|，后两者总重加x。用新数组转移保证每件一次。最后在0到m的差值中取最大总重。',
        r'''int n, m; cin >> n >> m; vector<int> a(n); int sum = 0; for (int &x : a) { cin >> x; sum += x; } vector<int> dp(sum + 1,-1); dp[0] = 0; int processed = 0; for (int x : a) { vector<int> next = dp; for (int d = 0; d <= processed; d++) if (dp[d] >= 0) { next[d + x] = max(next[d + x],dp[d] + x); next[abs(d - x)] = max(next[abs(d - x)],dp[d] + x); } processed += x; dp.swap(next); } cout << *max_element(dp.begin(),dp.begin() + min(sum,m) + 1);''',
        'm不是背包容量，是两侧重量差上限。必须允许武器暂不选择；同一件不可从本轮新状态再用一次。', complexity=r'总重量 $S\le10000$，时间 $O(nS)$，空间 $O(S)$。')
    put(13885, 1600, ['动态规划', '取模', '抽屉原理'], '每首歌至多一次，能否选非空集合使总秒数为3600的倍数。',
        '只关心和模3600，做非空子集余数DP。每首歌从旧状态转移，再单独加入只选此歌的余数。不能让空集合的余数0直接作为成功。\n\n若n≥3600，一定成功：取前3600首的3600个非空前缀和，若某个模3600为0已成功，否则这些前缀只落在3599种非零余数中，必有两者同余，其间连续一段和可整除3600。故只对n<3600做DP，大输入读完后直接输出YES。',
        r'''int tests; cin >> tests; while (tests--) { int n; cin >> n; vector<int> songs(n); for (int &x : songs) { cin >> x; x %= 3600; } if (n >= 3600) { cout << "YES\n"; continue; } bitset<3600> can; for (int x : songs) { bitset<3600> rotated = (can << x) | (can >> (3600 - x)); can |= rotated; can.set(x); if (can[0]) break; } cout << (can[0] ? "YES\n" : "NO\n"); }''',
        '目标是小时，不是分钟。移位循环旋转必须基于旧can；0秒余数的单首歌就可成功。', complexity=r'读取 $O(n)$；小规模用位集DP，时间 $O(n\lceil3600/w\rceil)$、额外状态 $O(3600)$ 位，其中 $w$ 为机器字长，输入数组 $O(n)$。')
    put(14704, 1800, ['01背包', '贪心', '动态规划'], '每道菜选择至多一次，越晚完成美味衰减越多，在时间内至少完整做一道，最大化总美味。',
        '先确定任意所选菜的最优顺序。比较相邻两菜i、j，i先做比j先做多得b[i]*c[j]−b[j]*c[i]，与此前累计时间无关。因此按b[i]*c[j]≥b[j]*c[i]排序，即衰减速度与耗时的比值递减，可通过相邻交换得到所有子集通用的最优顺序。\n\n再按此顺序做01背包。dp[t]表示选前面若干道菜、恰好用t时间的最大美味；选当前菜时，从dp[t−c]加a−t*b，t必须倒序以保证该道菜只做一次。dp[0]=0只作为开始状态，答案在t≥1中取最大，不能选空集。原题写原料无限，指同一原料可以供多种菜使用；样例2也排除了反复制作同一道菜的解释。',
        r'''int n, m, totalTime; cin >> n >> m >> totalTime; vector<long long> decay(n + 1); for (int i = 1; i <= n; i++) cin >> decay[i]; struct Dish { long long value, rate; int duration; }; vector<Dish> dishes(m); for (auto &d : dishes) { int ingredient; cin >> ingredient >> d.value >> d.duration; d.rate = decay[ingredient]; } sort(dishes.begin(),dishes.end(),[](const auto &a, const auto &b) { return a.rate * b.duration > b.rate * a.duration; }); const long long neg = -(1LL << 60); vector<long long> dp(totalTime + 1,neg); dp[0] = 0; for (auto d : dishes) for (int t = totalTime; t >= d.duration; t--) if (dp[t - d.duration] != neg) dp[t] = max(dp[t],dp[t - d.duration] + d.value - d.rate * t); cout << *max_element(dp.begin() + 1,dp.end());''',
        '用完成时刻而不是开始时刻扣衰减。不能将答案初始化为0，否则全部负收益时会错误选择不做菜。排序用交叉乘积，避免除零及浮点比较。', complexity=r'时间 $O(m\log m+mT)$，空间 $O(T+n+m)$。', cases=[{'input':'1 1 1\n100\n1 1 1','output':'-99'}])
    put(16671, 1700, ['分组背包', '依赖关系'], '附件必须连同所属主件购买，每主件最多两附件，最大化价格乘重要度之和。',
        '把一个主件及其附件组成一组。组内合法购买方案只有主件，以及主件搭配附件的所有子集，最多四种；不买整组也允许。逐主件做分组背包，预算倒序，枚举该组全部合法方案。每个方案一次性加入总价格和总价值，避免附件脱离主件。先读完全部物品，附件可能在主件前出现。',
        r'''int budget, n; cin >> budget >> n; vector<int> price(n + 1), value(n + 1), parent(n + 1); vector<vector<int>> attachment(n + 1); for (int i = 1; i <= n; i++) { int importance; cin >> price[i] >> importance >> parent[i]; value[i] = price[i] * importance; if (parent[i]) attachment[parent[i]].push_back(i); } vector<int> dp(budget + 1); for (int main = 1; main <= n; main++) if (!parent[main]) { vector<pair<int,int>> choices; int k = attachment[main].size(); for (int mask = 0; mask < (1 << k); mask++) { int cost = price[main], gain = value[main]; for (int j = 0; j < k; j++) if (mask >> j & 1) { int id = attachment[main][j]; cost += price[id]; gain += value[id]; } choices.push_back({cost,gain}); } for (int c = budget; c >= 0; c--) for (auto [cost,gain] : choices) if (cost <= c) dp[c] = max(dp[c],dp[c - cost] + gain); } cout << dp[budget];''',
        '不能对附件单独做普通01背包；必须与主件组合。预算倒序后，读取的较小预算仍是上一组状态。', complexity=r'每组至多4种选择，时间 $O(mB)$，空间 $O(m+B)$。')
    put(14699, 1700, ['01背包', '计数维度'], '最多选五名从者，礼装数量不能超过从者数量，总cost受限，最大化总攻击。',
        '从者和礼装之间没有指定兼容性，只要求一名从者最多配一礼装，故分别做“选择数量、恰好cost”的01背包。两边数量都只需0到5。最后枚举从者数s、礼装数e≤s及两边cost，总cost≤d时合并攻击值取最大。礼装能任意分给所选从者，因此数量约束已经充分，不必记录实际配对。',
        r'''int n, m, budget; cin >> n >> m >> budget; const int neg = -1000000000; auto build = [&](int items) { vector<vector<int>> dp(6,vector<int>(budget + 1,neg)); dp[0][0] = 0; while (items--) { int attack,cost; cin >> attack >> cost; for (int count = 5; count >= 1; count--) for (int b = budget; b >= cost; b--) if (dp[count - 1][b - cost] != neg) dp[count][b] = max(dp[count][b],dp[count - 1][b - cost] + attack); } return dp; }; auto servant = build(n), equipment = build(m); int answer = 0; for (int s = 1; s <= 5; s++) for (int e = 0; e <= s; e++) for (int a = 0; a <= budget; a++) if (servant[s][a] != neg) for (int b = 0; a + b <= budget; b++) if (equipment[e][b] != neg) answer = max(answer,servant[s][a] + equipment[e][b]); cout << answer;''',
        '不可单独上礼装，也不要求每个从者都穿礼装。数量和预算两维均倒序，保证物品各用一次。', complexity=r'时间 $O(5(n+m)d+25d^2)$，空间 $O(5d)$。')
    put(14701, 1700, ['区间动态规划', '滚动数组'], '每次从A的两端取一数，第i次乘B[i]，求全部取完的最大总值。',
        'dp[l][r]表示尚余A[l..r]时，从现在直到取完能获得的最大值。剩余长度len时，已经取了n−len个，所以当前乘数是B[n−len]。选择左端转到dp[l+1][r]，选择右端转到dp[l][r−1]，二者取最大。从长度1到n计算。滚动为dp[l]时，每一长度下l从小到大更新，dp[l]和dp[l+1]都仍是上一长度的值。',
        r'''int tests; cin >> tests; while (tests--) { int n; cin >> n; vector<long long> a(n), b(n), dp(n + 1); for (auto &x : a) cin >> x; for (auto &x : b) cin >> x; for (int length = 1; length <= n; length++) for (int l = 0; l + length <= n; l++) { int r = l + length - 1; long long multiplier = b[n - length]; dp[l] = max(a[l] * multiplier + dp[l + 1],a[r] * multiplier + dp[l]); } cout << dp[0] << '\n'; }''',
        '乘数取决于已取数量，不是剩余区间的左端点。滚动更新必须从小到大，反过来会读到本轮新状态。', complexity=r'每组时间 $O(n^2)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
