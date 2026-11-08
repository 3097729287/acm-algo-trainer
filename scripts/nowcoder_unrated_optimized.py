"""Finish all still-unrated eligible problems after full statement/PDF review."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_hull_support import HULL, HULL_EXPLANATION
from nowcoder_range_min_support import RANGE_MIN


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(17395,2200,['动态规划','单调队列'],'每段时间只沿固定方向滑行或停下，不能撞障碍，最大化总滑行格数。',
        '将同方向持续的时间合成一次转移。在这一方向的一条无障碍线上，沿运动方向给格子编号p。若本段至多D步，从q到p的贡献为p−q，且q在[p−D,p]内，于是new[p]=p+max(old[q]−q)。用单调队列维护这个滑动最大值。遇到障碍立刻清队列，禁止跨家具转移。\n\n向北按每列从下往上扫描，南反之；向西按每行从右往左，东反之。每段用完整旧数组生成新数组，允许q=p表示全程停住。初态只有起点分数0，其余不可达。每个时间段只扫一遍地图，最后取所有位置的最大分。',
        r'''int rows,cols,x,y,k; cin >> rows >> cols >> x >> y >> k; vector<string> grid(rows); for (auto &row : grid) cin >> row; const int neg = -1000000000; vector<int> dp(rows * cols,neg), next(dp.size()); dp[(x - 1) * cols + y - 1] = 0; while (k--) { int begin,end,direction; cin >> begin >> end >> direction; int duration = end - begin + 1; fill(next.begin(),next.end(),neg); auto process = [&](const vector<int> &line) { deque<pair<int,int>> queue; for (int p = 0; p < (int)line.size(); p++) { int cell = line[p]; if (grid[cell / cols][cell % cols] == 'x') { queue.clear(); continue; } while (!queue.empty() && queue.front().first < p - duration) queue.pop_front(); if (dp[cell] != neg) { int value = dp[cell] - p; while (!queue.empty() && queue.back().second <= value) queue.pop_back(); queue.push_back({p,value}); } if (!queue.empty()) next[cell] = p + queue.front().second; } }; if (direction <= 2) { for (int c = 0; c < cols; c++) { vector<int> line; line.reserve(rows); for (int p = 0; p < rows; p++) { int r = direction == 1 ? rows - 1 - p : p; line.push_back(r * cols + c); } process(line); } } else { for (int r = 0; r < rows; r++) { vector<int> line; line.reserve(cols); for (int p = 0; p < cols; p++) { int c = direction == 3 ? cols - 1 - p : p; line.push_back(r * cols + c); } process(line); } } dp.swap(next); } cout << *max_element(dp.begin(),dp.end());''',
        '每段允许的步数是end−begin+1。输出滑动格数，不是时间；施法停留不加分。队列必须在障碍处断开。',complexity=r'时间 $O(KNM)$，空间 $O(NM+\max(N,M))$。')
    put(20067,2200,['动态规划','斜率优化'],'连续玩具分箱，箱内相邻玩具间隔一单位，费用为箱长与L之差的平方，求最少费用。',
        r'令S[i]=前i件玩具长度和+i，分界在j后时，该箱长度为S[i]−S[j]−1。记x=S[i]−L−1，则dp[i]=x²+min(dp[j]+S[j]²−2S[j]x)。每个已求出的j是一条斜率−2S[j]、截距dp[j]+S[j]²的直线。S严格增加，所以斜率递减、查询x递增，可用单调凸壳线性完成。' + '\n\n' + HULL_EXPLANATION,
        r'''int n; long long target; cin >> n >> target; MonotoneHull hull; hull.add(0,0); Wide prefix = 0, best = 0; for (int i = 1; i <= n; i++) { long long length; cin >> length; prefix += length + 1; Wide x = prefix - target - 1; best = x * x + hull.minimum(x); hull.add(-2 * prefix,best + prefix * prefix); } printWide(best);''',
        '相邻填充物数量为本箱玩具数减一，所以常数是L+1。即使最终费用能装64位，前缀平方和交叉乘积也可能超出，必须先转128位。',
        declarations=HULL,complexity=r'时间 $O(n)$，空间 $O(n)$。')
    put(20384,2300,['动态规划','斜率优化'],'将连续路段分成恰好m天，最小化日路程方差，输出方差乘m²。',
        r'设总长S，m天路程为d[t]，方差乘m²等于m*Σd[t]²−S²，因此只需最小化每日路程平方和。用前缀和P，分层DP：new[i]=P[i]²+min(old[j]+P[j]²−2P[i]P[j])，j<i且j≥当前天数−1。每层重新建凸壳，直线斜率−2P[j]、截距old[j]+P[j]²，横坐标为P[i]。先查询再把j=i的旧层状态加入，确保每段至少有一个原路段。' + '\n\n' + HULL_EXPLANATION,
        r'''int n,days; cin >> n >> days; vector<Wide> prefix(n + 1); for (int i = 1; i <= n; i++) { long long x; cin >> x; prefix[i] = prefix[i - 1] + x; } const Wide inf = Wide(1) << 120; vector<Wide> previous(n + 1,inf), current(n + 1); previous[0] = 0; for (int day = 1; day <= days; day++) { fill(current.begin(),current.end(),inf); MonotoneHull hull; int initial = day - 1; hull.add(-2 * prefix[initial],previous[initial] + prefix[initial] * prefix[initial]); for (int i = day; i <= n; i++) { current[i] = prefix[i] * prefix[i] + hull.minimum(prefix[i]); if (previous[i] != inf) hull.add(-2 * prefix[i],previous[i] + prefix[i] * prefix[i]); } previous.swap(current); } printWide(days * previous[n] - prefix[n] * prefix[n]);''',
        '不能漏乘m或误输出普通方差。每一层只用旧层值建线；费用与坐标取128位，避免上界或乘积影响比较。',declarations=HULL,
        complexity=r'时间 $O(mn)$，空间 $O(n)$。')
    put(20601,2300,['动态规划','斜率优化'],'工厂产品只能往更大编号运，建仓库和运输均收费，求最低总成本。',
        r'令P[i]=Σp，W[i]=Σp*x。若上一仓库在j、下一仓库在i，把(j,i]产品运到i的费用为x[i]*(P[i]−P[j])−(W[i]−W[j])。所以dp[i]=c[i]+x[i]P[i]−W[i]+min(dp[j]+W[j]−x[i]P[j])。这是斜率−P[j]、截距dp[j]+W[j]、查询横坐标x[i]的直线最小值。工厂顺序向山下距离增加，P非减，符合单调凸壳。' + '\n\n' + HULL_EXPLANATION + '\n\n若后面工厂产品全为0，并不必须在那里再建仓库。因此答案取所有P[i]已等于总产品数的dp[i]最小；全无产品可不建仓，费用0。这样也覆盖零产品的边界情况。',
        r'''int n; cin >> n; struct Factory { long long x,p,c; }; vector<Factory> a(n); Wide total = 0; for (auto &f : a) { cin >> f.x >> f.p >> f.c; total += f.p; } if (total == 0) { cout << 0; return 0; } MonotoneHull hull; hull.add(0,0); Wide quantity = 0, weighted = 0, answer = Wide(1) << 120; for (auto f : a) { quantity += f.p; weighted += Wide(f.p) * f.x; Wide value = f.c + Wide(f.x) * quantity - weighted + hull.minimum(f.x); if (quantity == total) answer = min(answer,value); hull.add(-quantity,value + weighted); } printWide(answer);''',
        '不能把产品向上运，分组末端必须是所建仓库位置。产品数为0时出现相同斜率，保留截距较小者即可。',declarations=HULL,
        complexity=r'时间 $O(n)$，空间 $O(n)$。')
    put(51111,1600,['扫描线','区间合并'],'多个实数坐标矩形求并面积，多组0结束，严格按两位小数报告。',
        'n仅100，可把全部矩形左右边界排序去重，按相邻x坐标切成竖条。每条内部没有矩形边界，覆盖情况恒定：收集完全穿过这条竖条的矩形y区间，排序并合并得到总覆盖高度，乘条宽加入面积。各竖条互不重叠，所有矩形并集恰好被覆盖。无需对坐标取整，也无需开平面网格。',
        r'''int n,tc = 0; while (cin >> n && n) { struct Rectangle { long double x1,y1,x2,y2; }; vector<Rectangle> a(n); vector<long double> xs; for (auto &r : a) { cin >> r.x1 >> r.y1 >> r.x2 >> r.y2; xs.push_back(r.x1); xs.push_back(r.x2); } sort(xs.begin(),xs.end()); xs.erase(unique(xs.begin(),xs.end()),xs.end()); long double area = 0; for (size_t i = 1; i < xs.size(); i++) { vector<pair<long double,long double>> intervals; for (auto r : a) if (r.x1 <= xs[i - 1] && r.x2 >= xs[i]) intervals.push_back({r.y1,r.y2}); sort(intervals.begin(),intervals.end()); long double covered = 0, left = 0, right = 0; bool active = false; for (auto [l,r] : intervals) { if (!active) { left = l; right = r; active = true; } else if (l > right) { covered += right - left; left = l; right = r; } else right = max(right,r); } if (active) covered += right - left; area += (xs[i] - xs[i - 1]) * covered; } cout << "Test case #" << ++tc << '\n' << "Total explored area: " << fixed << setprecision(2) << area << "\n\n"; }''',
        '坐标不是整数，不能离散化后把下标差当实际长度。每组报告后输出空行，Test case #后没有冒号。',complexity=r'每组时间 $O(n^2\log n)$，空间 $O(n)$。',floating_output=True)
    put(51196,2300,['动态规划','单调栈','线段树','滑动窗口'],'切成若干连续段，每段和≤M，最小化每段最大值之和。',
        '设dp[i]为前i项最优值。末段在j后开始，转移为dp[j]+max(a[j+1..i])，并要求末段和≤M。非负数使合法j形成一段后缀，可双指针维护最早末段起点L。\n\n在段树的叶子j维护这个转移候选。追加a[i]时，先将新叶i−1置为dp[i−1]+a[i]。旧候选的最大值如何变化？用值递减的单调栈保存当前后缀最大值的分段。弹出位置p时，弹后栈顶q（无则0），原来以a[p]为最大值的分界j恰为[q,p−1]，这些叶统一增加a[i]−a[p]。弹完后压i，在允许分界区间[L−1,i−1]查询最小，即得dp[i]。每个下标只弹一次，总更新线性次，每次段树对数时间。',
        r'''int n; long long limit; cin >> n >> limit; vector<long long> a(n + 1), prefix(n + 1), dp(n + 1); bool possible = true; for (int i = 1; i <= n; i++) { cin >> a[i]; prefix[i] = prefix[i - 1] + a[i]; if (a[i] > limit) possible = false; } if (!possible) { cout << -1; return 0; } RangeMinimum tree(n); vector<int> stack; int left = 1; for (int i = 1; i <= n; i++) { while (!stack.empty() && a[stack.back()] <= a[i]) { int p = stack.back(); stack.pop_back(); int q = stack.empty() ? 0 : stack.back(); tree.add(1,0,n - 1,q,p - 1,a[i] - a[p]); } stack.push_back(i); tree.assign(1,0,n - 1,i - 1,dp[i - 1] + a[i]); while (prefix[i] - prefix[left - 1] > limit) left++; dp[i] = tree.query(1,0,n - 1,left - 1,i - 1); } cout << dp[n];''',
        '单个元素>M立即无解。M、前缀和、DP用64位；数组含0仍保持窗口合法性和单调栈分段。栈更新的是所有分界候选，不能只维护一个当前最大值。',declarations=RANGE_MIN,
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(20488,2100,['最小割','最大流','网格建图'],'网格各有固定狼领地、羊领地或空地，添最短单位篱笆让狼羊无法相通。',
        '把每格分到狼侧或羊侧，固定狼格必须在狼侧、固定羊格必须在羊侧，空地可任意选择。相邻两格若分到不同侧，就在它们公共边加一段篱笆，费用1。因此建源点连狼格无穷容量边，羊格连汇点无穷容量边，每对相邻格连两个方向各容量1。任意有限s-t割都保持固定领地，并恰为一组合法隔离篱笆，割容量就是长度，故求最大流即最短篱笆。外边界已有篱笆，不另加费用。',
        r'''int rows,cols; cin >> rows >> cols; int source = rows * cols, sink = source + 1; Dinic flow(sink + 1); vector<int> type(source); for (int &x : type) cin >> x; const int inf = 1000000000; for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) { int u = r * cols + c; if (type[u] == 1) flow.add(source,u,inf); if (type[u] == 2) flow.add(u,sink,inf); if (r + 1 < rows) { int v = u + cols; flow.add(u,v,1); flow.add(v,u,1); } if (c + 1 < cols) { int v = u + 1; flow.add(u,v,1); flow.add(v,u,1); } } cout << flow.maximum(source,sink);''',
        '固定狼羊格不能互换，必须用足够大的容量锁定。相邻无向公共边建两条容量1有向边，割时只计狼侧到羊侧的一个方向。',
        declarations=r'''struct Dinic { struct Edge { int to,reverse,capacity; }; vector<vector<Edge>> graph; vector<int> level,current; explicit Dinic(int n) : graph(n),level(n),current(n) {} void add(int a,int b,int c) { int x = graph[a].size(), y = graph[b].size(); graph[a].push_back({b,y,c}); graph[b].push_back({a,x,0}); }
        bool bfs(int source,int sink) { fill(level.begin(),level.end(),-1); vector<int> queue{source}; level[source] = 0; for (size_t h = 0; h < queue.size(); h++) for (auto e : graph[queue[h]]) if (e.capacity && level[e.to] == -1) { level[e.to] = level[queue[h]] + 1; queue.push_back(e.to); } return level[sink] != -1; }
        int send(int u,int sink,int amount) { if (u == sink) return amount; for (int &i = current[u]; i < (int)graph[u].size(); i++) { auto &e = graph[u][i]; if (e.capacity && level[e.to] == level[u] + 1) { int value = send(e.to,sink,min(amount,e.capacity)); if (value) { e.capacity -= value; graph[e.to][e.reverse].capacity += value; return value; } } } return 0; }
        int maximum(int source,int sink) { int total = 0; while (bfs(source,sink)) { fill(current.begin(),current.end(),0); while (int value = send(source,sink,1000000000)) total += value; } return total; } };''',
        complexity=r'格点数 $V=nm$、邻边数 $E=O(V)$，一般Dinic最坏时间 $O(V^2E)$，实际由网格容量层次推进；空间 $O(V+E)$。')


if __name__ == '__main__':
    run()
