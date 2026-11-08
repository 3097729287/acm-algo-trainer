"""Sparse shortest paths, metric MSTs and exact numeric graph objectives."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_dsu_support import DSU
from nowcoder_graph_support import DIJKSTRA
from nowcoder_tree_support import TREE


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(16541, 1900, ['拓扑排序', '差分约束', '虚拟结点'], '每趟车停站的级别高于区间内全部不停站，求最少等级。',
        '对每趟车引入一个虚拟结点：区间内每个不停站向虚拟点连权0边，虚拟点向每个停站连权1边，表示后者等级至少比前者高1。这样每趟只连O(n)条边，避免所有不停站与停站两两连边。输入保证约束可满足，所以图是DAG。原车站初始等级1，虚拟点初始0，拓扑排序时做最长路转移level[v]=max(level[v],level[u]+w)。最终原车站最大等级就是最少分级数。',
        r'''int n,m; cin >> n >> m; vector<vector<pair<int,int>>> graph(n + m); vector<int> degree(n + m), level(n + m); fill(level.begin(),level.begin() + n,1); auto addEdge = [&](int a, int b, int w) { graph[a].push_back({b,w}); degree[b]++; }; for (int train = 0; train < m; train++) { int count; cin >> count; vector<int> stops(count); vector<bool> stopped(n); for (int &x : stops) { cin >> x; --x; stopped[x] = true; } int virtualNode = n + train; for (int x = stops.front(); x <= stops.back(); x++) if (!stopped[x]) addEdge(x,virtualNode,0); for (int x : stops) addEdge(virtualNode,x,1); } vector<int> queue; for (int u = 0; u < n + m; u++) if (!degree[u]) queue.push_back(u); for (size_t h = 0; h < queue.size(); h++) { int u = queue[h]; for (auto [v,w] : graph[u]) { level[v] = max(level[v],level[u] + w); if (--degree[v] == 0) queue.push_back(v); } } cout << *max_element(level.begin(),level.begin() + n);''',
        '只约束始发和终点之间的站。虚拟点的入边权0、出边权1，一条高一级约束不能被算成两级。', complexity=r'时间、空间均为 $O(nm+n+m)$。')
    put(14352, 1700, ['Dijkstra', '枚举'], '选三个不同景点A、B、C，司机每段走最短路，最大化两段最短路之和。',
        '枚举中转景点B，对稀疏无向图做一次Dijkstra。起点和终点只需是与B连通、不同于B的两个最远景点，因此取距离最大的两项相加。它们下标不同，由每个点只扫描一次保证。若任何B都没有两个可达其他点，就不存在合法三点方案，输出−1。无须三重枚举，也不适合对1000点稀疏图做Floyd。',
        r'''int tests; cin >> tests; while (tests--) { int n,m; cin >> n >> m; vector<vector<pair<int,long long>>> graph(n); while (m--) { int a,b; long long w; cin >> a >> b >> w; --a; --b; graph[a].push_back({b,w}); graph[b].push_back({a,w}); } long long answer = -1; for (int center = 0; center < n; center++) { auto d = dijkstra(graph,center); long long first = -1, second = -1; for (int u = 0; u < n; u++) if (u != center && d[u] != (1LL << 60)) { if (d[u] > first) { second = first; first = d[u]; } else if (d[u] > second) second = d[u]; } if (second != -1) answer = max(answer,first + second); } cout << answer << '\n'; }''',
        '不能把不可达的无穷距离当成最大值。两个不同景点距离相同也允许分别作为两端。', declarations=DIJKSTRA,
        complexity=r'每组时间 $O(n(n+m)\log n)$，空间 $O(n+m)$。')
    put(15479, 2000, ['Dijkstra', '位运算', '隐式图'], '任意两城可按异或值乘C直达，另有单向快捷边，求最短时间。',
        '把一次异或跳跃拆成若干次单比特翻转，第b位翻转费用2^b*C，翻转不同位的费用和恰为(u xor v)*C。为使任何两个真实城市都能这样连接，把编号扩到包含N的完整二进制立方体0到2^B−1，扩展编号仅作中间点，不新增快捷边。\n\n扩展不会凭空变便宜：任何纯翻位路径在每个差异位至少付一次，所以其费用不低于两端原有直达边；一段经过虚拟点的路径可替换成对应真实城市间直达。因此最优值保持。Dijkstra中按需生成B条翻位邻边，再处理当前真实城市的快捷边，无需显式建立完全图。',
        r'''int n,m; long long c; cin >> n >> m >> c; int size = 1; while (size <= n) size <<= 1; vector<vector<pair<int,long long>>> quick(size); while (m--) { int a,b; long long w; cin >> a >> b >> w; quick[a].push_back({b,w}); } int start,target; cin >> start >> target; const long long inf = 1LL << 60; vector<long long> distance(size,inf); priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>> heap; distance[start] = 0; heap.push({0,start}); while (!heap.empty()) { auto [cost,u] = heap.top(); heap.pop(); if (cost != distance[u]) continue; if (u == target) break; auto relax = [&](int v, long long w) { if (distance[v] > cost + w) { distance[v] = cost + w; heap.push({distance[v],v}); } }; for (int bit = 1; bit < size; bit <<= 1) relax(u ^ bit,bit * c); for (auto [v,w] : quick[u]) relax(v,w); } cout << distance[target];''',
        '虚拟编号0和大于N的编号要保留，否则某些异或直达无法拆成等价路径。快捷通道只按给定方向添加。', complexity=r'$V=2^{\lceil\log_2(N+1)\rceil}<2(N+1)$，时间 $O((V\log V+M)\log V)$，空间 $O(V+M)$。')
    put(17509, 1400, ['最小生成树', '并查集'], '用最少沟数连通所有据点，再最小化沟的总长度。',
        '连通n个点至少需要n−1条边；达到该数量的连通图就是生成树。因此按边长排序，Kruskal每次加入连接不同连通块的最短边，累计长度，选满n−1条结束。切分性质保证每次选择可属于某棵最小生成树。题目保证原图可连通。',
        r'''int n,m; cin >> n >> m; struct Edge { int a,b,w; }; vector<Edge> edges(m); for (auto &e : edges) cin >> e.a >> e.b >> e.w; sort(edges.begin(),edges.end(),[](auto a, auto b) { return a.w < b.w; }); DSU dsu(n); long long answer = 0; int used = 0; for (auto e : edges) if (dsu.unite(e.a,e.b)) { answer += e.w; if (++used == n - 1) break; } cout << answer;''',
        '重边可保留，形成环的边不选。目标是所挖沟的长度和，不是树上任意点对距离总和，样例3点答案7据此理解。', declarations=DSU,
        complexity=r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。')
    put(53074, 1900, ['最小生成树', '并查集', '分组'], '删除最小权值总和的边，让原MST权值不变且MST唯一。',
        '按权值分组Kruskal。进入权值w组前，先按更小权边收缩连通块。组内两端已在同一旧块的边永远不在任何MST中，可保留；其余候选边若在收缩图中有环，环上等权边可替换，MST就不唯一。必须把这些候选边删成森林，最少删除数为候选边数减该组的连通秩。\n\n先完整收集本组所有候选边，再对它们做并查集合并。成功合并的数就是秩，失败合并的候选边各必须删除一条，费用同为w，累计即可。收缩图每个分量保留任意生成树都能使后续Kruskal连通关系不变，所以原MST权值保持。',
        r'''int n,m; cin >> n >> m; struct Edge { int a,b; long long w; }; vector<Edge> edges(m); for (auto &e : edges) cin >> e.a >> e.b >> e.w; sort(edges.begin(),edges.end(),[](auto a, auto b) { return a.w < b.w; }); DSU dsu(n); long long answer = 0; for (int l = 0; l < m;) { int r = l; while (r < m && edges[r].w == edges[l].w) r++; vector<pair<int,int>> candidates; for (int i = l; i < r; i++) { int a = dsu.find(edges[i].a), b = dsu.find(edges[i].b); if (a != b) candidates.push_back({a,b}); } for (auto [a,b] : candidates) if (!dsu.unite(a,b)) answer += edges[l].w; l = r; } cout << answer;''',
        '必须在合并本组任何边之前筛候选，不能把本组造成的同根误认为更小权已经连通。原来就不是MST候选的重边或环边无需删除。', declarations=DSU,
        complexity=r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。')
    put(15108, 1300, ['最小生成树', '并查集'], '预算内能否修路连通全部城市，允许重边，多组。',
        'Kruskal求最小生成树总费用，选不到m−1条边说明图不连通；选满且总费用不超过预算则Yes，否则No。只判断费用而忽略是否连通，会把便宜但缺路的图误判成功。',
        r'''long long budget; int roads,cities; while (cin >> budget >> roads >> cities) { struct Edge { int a,b,w; }; vector<Edge> edges(roads); for (auto &e : edges) cin >> e.a >> e.b >> e.w; sort(edges.begin(),edges.end(),[](auto a, auto b) { return a.w < b.w; }); DSU dsu(cities); long long total = 0; int used = 0; for (auto e : edges) if (dsu.unite(e.a,e.b)) { total += e.w; used++; } cout << (used == cities - 1 && total <= budget ? "Yes\n" : "No\n"); }''',
        '输入顺序是预算、道路数、城市数。预算恰好够也成功，输出大小写为Yes/No。', declarations=DSU,
        complexity=r'每组时间 $O(R\log R+(V+R)\alpha(V))$，空间 $O(V+R)$。')
    put(52867, 2000, ['树的直径', '最大生成树', '树上距离'], '完全图的边权为原树两点距离，求最大生成树的总权。',
        '求原树直径端点A、B。树的非负边权保证任一点v的最远点可在A、B中取，所以偏心距ecc[v]=max(distA[v],distB[v])。先连A、B，其余每点连到较远端点，得到一棵树，总权为Σecc[v]−直径长度。\n\n上界也恰为此值：任意生成树以A为根，每个v≠A的父边至多ecc[v]，所以总权≤Σ(v≠A)ecc[v]=Σecc[v]−dist(A,B)。上述构造达到上界，因此最优。三次迭代树遍历先找A，再求distA并找B，最后求distB。',
        r'''int n; while (cin >> n) { Tree tree(n); for (int i = 1; i < n; i++) { int a,b; long long w; cin >> a >> b >> w; tree.add(a - 1,b - 1,w); } auto distances = [&](int source) { vector<long long> d(n,-1); vector<int> queue{source}; d[source] = 0; for (size_t h = 0; h < queue.size(); h++) { int u = queue[h]; for (auto [v,w] : tree.edge[u]) if (d[v] == -1) { d[v] = d[u] + w; queue.push_back(v); } } return d; }; auto first = distances(0); int a = max_element(first.begin(),first.end()) - first.begin(); auto da = distances(a); int b = max_element(da.begin(),da.end()) - da.begin(); auto db = distances(b); long long answer = -da[b]; for (int u = 0; u < n; u++) answer += max(da[u],db[u]); cout << answer << '\n'; }''',
        '求的是最大生成树，不能直接把原树边权相加。原树路径唯一，用普通遍历累加距离即可，无须Dijkstra。', declarations=TREE,
        complexity=r'每组时间、空间均为 $O(n)$。')
    put(26257, 1900, ['Dijkstra', '分层图', '状态建模'], '地铁每次上线路付固定费，在线路内每走相邻一站付单位费，可换乘，求最便宜路线。',
        '把原站点当作“已下车”结点，给每个(线路,站点)新建一个车上结点。原站→车上结点权为该线路固定上车费，车上→原站权0；同线路相邻车上结点双向连每站费用b。这样可持续坐同一条线而不重复付上车费，换线则必须重新付对应费用。每站费用按线路站序算，不按原站编号差。扩展图规模与总线路站数线性，Dijkstra求原站s到t。',
        r'''int n,m,s,t; cin >> n >> m >> s >> t; vector<vector<pair<int,long long>>> graph(n); for (int line = 0; line < m; line++) { long long board,step; int count; cin >> board >> step >> count; int previous = -1; while (count--) { int station; cin >> station; --station; int node = graph.size(); graph.emplace_back(); graph[station].push_back({node,board}); graph[node].push_back({station,0}); if (previous != -1) { graph[previous].push_back({node,step}); graph[node].push_back({previous,step}); } previous = node; } } auto d = dijkstra(graph,s - 1); cout << (d[t - 1] == (1LL << 60) ? -1 : d[t - 1]);''',
        '固定费每次上车收，不是整趟行程只收一次。s=t可不乘车，答案0。', declarations=DIJKSTRA,
        complexity=r'总线路站数 $L$，时间 $O((n+L)\log(n+L))$，空间 $O(n+L)$。')
    put(24858, 1700, ['Bellman-Ford', '正环检测'], '每到一城可赚D，路免费、航线收费且可借款，求最大余额或可无限赚钱。',
        '初始在S先赚D。免费道路u→v增加D，航线增加D−票价，问题变为从S出发可随时结束的最长收益路。用Bellman-Ford最大化余额，仅从可达状态松弛。若第C轮仍有更新，存在从S可达的正收益环，可以无限重复，输出−1；否则最优路可删掉非正环，至多C−1条边，取所有城市余额最大值。允许用未来收入付机票，所以中间余额可为负，不能限制边的可走性。',
        r'''int income,p,n,f,start; cin >> income >> p >> n >> f >> start; struct Edge { int a,b,gain; }; vector<Edge> edges; for (int i = 0; i < p; i++) { int a,b; cin >> a >> b; edges.push_back({a - 1,b - 1,income}); } for (int i = 0; i < f; i++) { int a,b,price; cin >> a >> b >> price; edges.push_back({a - 1,b - 1,income - price}); } const long long neg = -(1LL << 60); vector<long long> best(n,neg); best[start - 1] = income; bool unlimited = false; for (int round = 1; round <= n; round++) { bool changed = false; for (auto e : edges) if (best[e.a] != neg && best[e.b] < best[e.a] + e.gain) { best[e.b] = best[e.a] + e.gain; changed = true; } if (!changed) break; if (round == n) unlimited = true; } cout << (unlimited ? -1 : *max_element(best.begin(),best.end()));''',
        '只需任意可达正环，不要求还能去某个指定终点。无法从S到达的正环不影响答案。起始城市的D也计入。', complexity=r'时间 $O(C(P+F))$，空间 $O(C+P+F)$。')
    put(24755, 1400, ['Dijkstra', '枚举顺序'], '从PB出发，把苹果送到PA1、PA2，先后任选，不需回起点。',
        '仅两种顺序：PB→PA1→PA2，或PB→PA2→PA1。图无向，两目标间距离共用，答案为dist(PA1,PA2)+min(dist(PB,PA1),dist(PB,PA2))。分别从两个目标做Dijkstra即可取得这三个距离。',
        r'''int m,n,start,a,b; cin >> m >> n >> start >> a >> b; --start; --a; --b; vector<vector<pair<int,long long>>> graph(n); while (m--) { int u,v; long long w; cin >> u >> v >> w; --u; --v; graph[u].push_back({v,w}); graph[v].push_back({u,w}); } auto da = dijkstra(graph,a), db = dijkstra(graph,b); cout << da[b] + min(da[start],db[start]);''',
        '首行先给道路数C，再给草地数P。距离和保证输入边总长不超过二十亿，但组合运算仍使用64位。', declarations=DIJKSTRA,
        complexity=r'时间 $O((P+C)\log P)$，空间 $O(P+C)$。')
    put(24370, 1800, ['Dijkstra', '枚举瓶颈'], '路径耗时为延迟和加X除以最小容量，求最小耗时向下取整。',
        '最优路径的瓶颈容量一定等于某条边容量。枚举容量下限c，只用容量≥c的边，Dijkstra求最小延迟L，再用L+floor(X/c)更新答案。若实际路径容量更大，本轮估计只会偏大；而枚举到其真实瓶颈时会得到不差于最优路径的延迟，因此最终恰为最优。所有候选的向下取整可先做再取最小，无需浮点。',
        r'''int n,m; long long milk; cin >> n >> m >> milk; struct Edge { int to,latency,capacity; }; vector<vector<Edge>> graph(n); vector<int> capacities; while (m--) { int a,b,l,c; cin >> a >> b >> l >> c; --a; --b; graph[a].push_back({b,l,c}); graph[b].push_back({a,l,c}); capacities.push_back(c); } if (n == 1) { cout << 0; return 0; } sort(capacities.begin(),capacities.end()); capacities.erase(unique(capacities.begin(),capacities.end()),capacities.end()); const long long inf = 1LL << 60; long long answer = inf; for (int threshold : capacities) { vector<long long> distance(n,inf); priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>> heap; distance[0] = 0; heap.push({0,0}); while (!heap.empty()) { auto [cost,u] = heap.top(); heap.pop(); if (cost != distance[u]) continue; if (u == n - 1) break; for (auto e : graph[u]) if (e.capacity >= threshold && distance[e.to] > cost + e.latency) { distance[e.to] = cost + e.latency; heap.push({distance[e.to],e.to}); } } if (distance[n - 1] != inf) answer = min(answer,distance[n - 1] + milk / threshold); } cout << (answer == inf ? -1 : answer);''',
        '不能只求一次最短延迟后再算容量；更长延迟可能换来更大容量。原题输出向下取整，不四舍五入。', complexity=r'不同容量数 $K\le M$，时间 $O(K(N+M)\log N)$，空间 $O(N+M)$。')
    put(25077, 1300, ['Dijkstra', '往返距离'], '聚会暂停等所有奶牛各自回家拿东西再回来，求最早恢复时间，道路双向。',
        '所有牛同时出发，各自往返最优时间为2*dist(X,家)。只需等最慢的一头，故从X做一次Dijkstra，最大距离乘二。重边直接保留，最短路会自动选更好者。',
        r'''int n,m,x; cin >> n >> m >> x; vector<vector<pair<int,long long>>> graph(n); while (m--) { int a,b; long long w; cin >> a >> b >> w; --a; --b; graph[a].push_back({b,w}); graph[b].push_back({a,w}); } auto d = dijkstra(graph,x - 1); cout << 2 * *max_element(d.begin(),d.end());''',
        '本题是双向Bronze Cow Party，不要误用另一道有向往返聚会题的输入方向。暂停时间取最大，不是各牛时间总和。', declarations=DIJKSTRA,
        complexity=r'时间 $O((N+M)\log N)$，空间 $O(N+M)$。')
    put(25005, 1400, ['Floyd', '最短路'], '必须按指定顺序经过岛屿，可绕行其他岛屿，最小化危险值总和。',
        '先Floyd求任意两岛间最小危险值。相邻两个指定目的地之间的绕行互不限制，可分别取最短路，再将整个指定序列的相邻距离相加。重复经过其他目的地并不妨碍之后按序正式到访，因此不必限制中间结点。',
        r'''int n,m; cin >> n >> m; vector<int> order(m); for (int &x : order) { cin >> x; --x; } vector<vector<long long>> distance(n,vector<long long>(n)); for (auto &row : distance) for (auto &x : row) cin >> x; for (int k = 0; k < n; k++) for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) distance[i][j] = min(distance[i][j],distance[i][k] + distance[k][j]); long long answer = 0; for (int i = 1; i < m; i++) answer += distance[order[i - 1]][order[i]]; cout << answer;''',
        '访问序列不能自行排序。即使经过指定序列后面的岛，也可之后再回去，题目允许多次访问。', complexity=r'时间 $O(n^3+m)$，空间 $O(n^2+m)$。')
    put(25020, 1400, ['Floyd', '瓶颈路径'], '有向图多次查询，使路径最大障碍高度最小，不可达输出负一。',
        '将Floyd的加法换成取最大：经过中间点k的瓶颈为max(d[i][k],d[k][j])，再与原d[i][j]取最小。初始直接边取其高度，重边保留较小者，自己到自己为0。三重循环后得到所有最小瓶颈路径。不可达用无穷，自然不会改善正常值。',
        r'''int n,m,q; cin >> n >> m >> q; const int inf = 1000000000; vector<vector<int>> d(n,vector<int>(n,inf)); for (int i = 0; i < n; i++) d[i][i] = 0; while (m--) { int a,b,w; cin >> a >> b >> w; --a; --b; d[a][b] = min(d[a][b],w); } for (int k = 0; k < n; k++) for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) d[i][j] = min(d[i][j],max(d[i][k],d[k][j])); while (q--) { int a,b; cin >> a >> b; int answer = d[a - 1][b - 1]; cout << (answer == inf ? -1 : answer) << '\n'; }''',
        '边是单向的。目标是最大障碍的高度，不是沿途高度之和。Floyd中间点k必须放最外层。', complexity=r'时间 $O(N^3+T)$，空间 $O(N^2)$。')
    put(208246, 1500, ['Dijkstra', '方向状态'], '迷宫中四方向移动，起终朝向任意，最少需要转多少个90度弯。',
        '状态为(格子,面向方向)，移动到方向d的邻格时，费用为旧朝向与d之间的最少四分之一圈数：相同0、垂直1、相反2。起点四个方向都初始化为0，表示初始朝向任意。Dijkstra求所有方向状态的最少转角次数，终点取四个方向最小。按每步代价建模，比只在格子上记录一个最优值准确，因为相同格子的不同朝向会影响后续费用。',
        r'''int n; cin >> n; vector<char> cells; string token; while ((int)cells.size() < n * n && cin >> token) { size_t p; while ((p = token.find(u8"…")) != string::npos) token.replace(p,string(u8"…").size(),"..."); for (char c : token) if (c == '.' || c == 'x' || c == 'A' || c == 'B') cells.push_back(c); } int start = 0, target = 0; for (int i = 0; i < n * n; i++) { if (cells[i] == 'A') start = i; if (cells[i] == 'B') target = i; } const int inf = 1000000000; vector<int> distance(4 * n * n,inf); priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> heap; for (int d = 0; d < 4; d++) { distance[start * 4 + d] = 0; heap.push({0,start * 4 + d}); } int dr[] = {-1,0,1,0}, dc[] = {0,1,0,-1}; while (!heap.empty()) { auto [cost,state] = heap.top(); heap.pop(); if (cost != distance[state]) continue; int u = state / 4, facing = state % 4, r = u / n, c = u % n; for (int d = 0; d < 4; d++) { int rr = r + dr[d], cc = c + dc[d]; if (rr < 0 || rr >= n || cc < 0 || cc >= n || cells[rr * n + cc] == 'x') continue; int difference = abs(d - facing), turn = min(difference,4 - difference), next = (rr * n + cc) * 4 + d; if (distance[next] > cost + turn) { distance[next] = cost + turn; heap.push({distance[next],next}); } } } int answer = *min_element(distance.begin() + target * 4,distance.begin() + target * 4 + 4); cout << (answer == inf ? -1 : answer);''',
        '输入可能是逐字符带空格，也可能整行连续字符，读取词后逐字符展开均可。起点朝向不能固定成一个方向。', complexity=r'时间 $O(N^2\log N)$，空间 $O(N^2)$。')
    if 'nowcoder-global::212331' not in existing:
        reviewed_clone(212331, 208246, '完整核对USACO障碍训练与转弯最少模型；本题保证可达，原样例用Unicode省略号表示一行三个点，代码明确展开后读取，正常地图字符仍逐格处理。')
    put(16466, 1500, ['函数图', '拓扑剥叶', '环检测'], '每人把信息传给固定对象，最早何时有人听回自己的生日。',
        '每点只有一条出边，自己的信息绕环一周才可能回到自己，所以答案是函数图最短有向环长。先统计入度，拓扑删除全部入度0点及随之变成0的点；剩下的点恰为各个互不相交的环。对每个未处理剩余点沿出边走一周计长，取最小。',
        r'''int n; cin >> n; vector<int> next(n), degree(n); for (int &v : next) { cin >> v; --v; degree[v]++; } vector<int> queue; for (int u = 0; u < n; u++) if (!degree[u]) queue.push_back(u); for (size_t h = 0; h < queue.size(); h++) if (--degree[next[queue[h]]] == 0) queue.push_back(next[queue[h]]); int answer = n; for (int u = 0; u < n; u++) if (degree[u]) { int length = 0, v = u; do { degree[v] = 0; length++; v = next[v]; } while (v != u); answer = min(answer,length); } cout << answer;''',
        '树枝上的信息只会进入环而不会回到自己，不影响最早轮数。不是求最长环，也不是数所有环节点。', complexity=r'时间、空间均为 $O(n)$。')
    put(25064, 1700, ['传递闭包', '位集'], '已有部分产奶高低关系，预先固定追加比较清单，保证比较后能完全排序，求最少对数。',
        '先求已有大小关系的传递闭包。已能比较的点对无需询问；每个互不可比点对都必须在固定清单中比较：对任意这样的a、b，可将二者共同前驱先排好，再令a、b相邻，分别交换它们可得两个符合全部旧关系的全序。它们对除(a,b)外所有点对的比较结果都相同，因此漏掉该对就无法保证区分。故答案正是不可比无序对数。\n\n用bitset维护每点能到的低排名点，Floyd发现i能到k时，将k的整个集合并给i，字长并行加速。',
        r'''int n,m; cin >> n >> m; vector<bitset<1000>> reach(n); while (m--) { int a,b; cin >> a >> b; reach[a - 1][b - 1] = 1; } for (int k = 0; k < n; k++) for (int i = 0; i < n; i++) if (reach[i][k]) reach[i] |= reach[k]; int answer = 0; for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++) if (!reach[a][b] && !reach[b][a]) answer++; cout << answer;''',
        '清单要事先固定并保证所有可能答案都能排序，因此不是自适应比较排序所需次数。每对只按a<b统计一次。', complexity=r'机器字长 $w$，时间 $O(n^3/w+n^2)$，空间 $O(n^2)$ 位。')
    put(14700, 1500, ['分层动态规划', '最短路'], '每条路走一天，抓人须不晚于k天，路费加每天累计挥霍最少。',
        'dp[d][v]为恰走d天到v的最少总损失。由前一天道路另一端转移，加本条路费和第d天的挥霍a[d]。每轮用新数组，避免同一天走多条路。终点可能早到更省，也可能走便宜的多段路更省，答案取0到k天所有终点状态的最小值。初态在1号城为0；n=1时可在第0天抓到。',
        r'''int n,m,k; cin >> n >> m >> k; struct Edge { int a,b,w; }; vector<Edge> edges(m); for (auto &e : edges) { cin >> e.a >> e.b >> e.w; --e.a; --e.b; } vector<int> waste(k + 1); for (int d = 1; d <= k; d++) cin >> waste[d]; const long long inf = 1LL << 60; vector<long long> dp(n,inf); dp[0] = 0; long long answer = dp[n - 1]; for (int day = 1; day <= k; day++) { vector<long long> next(n,inf); for (auto e : edges) { if (dp[e.a] != inf) next[e.b] = min(next[e.b],dp[e.a] + e.w + waste[day]); if (dp[e.b] != inf) next[e.a] = min(next[e.a],dp[e.b] + e.w + waste[day]); } dp.swap(next); answer = min(answer,dp[n - 1]); } cout << (answer == inf ? -1 : answer);''',
        '第d天的挥霍在所有当日转移中只加一次；不能只加到达那天的挥霍而漏掉之前各天。', complexity=r'时间 $O(k(n+m))$，空间 $O(n+m+k)$。')
    put(50385, 1500, ['Bellman-Ford', '负环检测'], '道路花正时间，虫洞倒退时间，判断图中任意位置是否存在可回到出发前的行程。',
        '给双向路加两条正权边，虫洞加一条负权有向边。回到出发前等价于存在负环。起点不限，所以将所有点初始距离设0，相当于超级源向全图连0边。Bellman-Ford若第N轮仍有松弛则有负环，提前一轮不变则无负环。只从1号点开始会漏掉其他连通块的虫洞环。',
        r'''int tests; cin >> tests; while (tests--) { int n,m,w; cin >> n >> m >> w; struct Edge { int a,b,w; }; vector<Edge> edges; while (m--) { int a,b,c; cin >> a >> b >> c; edges.push_back({a - 1,b - 1,c}); edges.push_back({b - 1,a - 1,c}); } while (w--) { int a,b,c; cin >> a >> b >> c; edges.push_back({a - 1,b - 1,-c}); } vector<long long> d(n); bool cycle = false; for (int round = 1; round <= n; round++) { bool changed = false; for (auto e : edges) if (d[e.b] > d[e.a] + e.w) { d[e.b] = d[e.a] + e.w; changed = true; } if (!changed) break; if (round == n) cycle = true; } cout << (cycle ? "YES\n" : "NO\n"); }''',
        '虫洞时间输入是回退的正数，存边时取负。判断全图负环，不要求与某个指定起点连通。', complexity=r'每组时间 $O(N(2M+W))$，空间 $O(N+M+W)$。')


if __name__ == '__main__':
    run()
