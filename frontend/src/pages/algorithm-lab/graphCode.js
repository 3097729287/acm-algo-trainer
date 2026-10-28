// These classroom fragments use the same state names as the experiments.
export const GRAPH_CODE={bfs:`// n 个顶点编号为 [0,n)，adj[u] 存 u 的所有邻点，start 为起点。
// dist[v]：最少走几条边到 v；-1 既表示不可达，也表示尚未发现。
// parent[v]：首次发现 v 的前驱；沿它逆向走可以还原最短路径。
vector<int> dist(n, -1), parent(n, -1);
queue<int> q; // 先进先出：第 d 层处理完，才会处理第 d+1 层。
dist[start] = 0; q.push(start); // 起点到自己为 0 步，前驱保留 -1。
while (!q.empty()) {
    int u = q.front(); q.pop(); // 取出当前层最早发现的顶点。
    for (int v : adj[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1; // 第一次发现就是无权图最短距离。
        parent[v] = u; // 距离与前驱在同一次发现中一起确定。
        q.push(v); // 入队前已标记，因此每个点只会入队一次。
    }
}`,dfs:`// visited 初始全 false，parent 初始全 -1；adj 是邻接表。
// 显式递归帧：（当前点，下一条待检查邻边的下标）。
// st 从底到顶恰好是当前 DFS 路径，可以避免深递归耗尽调用栈。
vector<pair<int,int>> st{{start, 0}};
visited[start] = true; // 入栈时标记，环和无向图的反向边不会重复进入。
while (!st.empty()) {
    int u = st.back().first; // 暂停在 u 的这一次递归调用。
    int &next = st.back().second; // 引用使下标更新留在原来的栈帧里。
    if (next == adj[u].size()) {
        // u 的所有子分支已完成；子树汇总等“退出时工作”放在这里。
        st.pop_back(); // 模拟函数返回，父帧会从暂停的邻边继续。
        continue;
    }
    int v = adj[u][next++]; // 先推进父帧的游标，再考虑进入子点。
    if (visited[v]) continue; // 已访问点不再产生新的递归帧。
    visited[v] = true;
    parent[v] = u; // 记录 DFS 树边；它一般不代表最短路径。
    st.push_back({v, 0}); // 进入 v，从它的第 0 条邻边开始。
    // push_back 可能扩容；本轮不再使用上面的 next 引用。
}`,dsu:`// 准备 vector<int> parent(n), size(n,1)，顶点编号为 [0,n)。
// 初始化：iota(parent.begin(), parent.end(), 0);
// parent[x] 是父指针；根满足 parent[x]==x；size 只在根上有效。
int find(int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]]; // 路径折半：将 x 挂到祖父。
        x = parent[x]; // 继续走向根；集合成员没有改变。
    }
    return x; // 根的编号只代表集合，不必是最小顶点。
}
bool unite(int a, int b) {
    a = find(a); b = find(b); // 合并的是两个完整集合，先转换成根。
    if (a == b) return false; // 已连通时不重复累加大小。
    if (size[a] < size[b]) swap(a, b); // 小树挂大树，限制树高。
    parent[b] = a; // b 不再是根，两个集合从此连通。
    size[a] += size[b]; // 合并后的大小只维护在新根 a 上。
    return true; // 可用于判断 Kruskal 是否成功选择了一条边。
}`,dijkstra:`// adj[u] 存（终点 v，非负边权 w）；start 是起点，编号为 [0,n)。
// 本片段要求最短距离小于 INF，且尝试的 du+w 不超过 long long。
using ll = long long; // 路径总权重可能超过 32 位整数。
const ll INF = (1LL << 62); // 区分“暂时不可达”与任意合法距离。
vector<ll> dist(n, INF); // dist[v] 是目前找到的最短候选距离。
vector<int> parent(n, -1); // 松弛成功时的前驱，用于还原路径。
priority_queue<pair<ll,int>, vector<pair<ll,int>>,
               greater<pair<ll,int>>> pq; // 小根堆，先按距离取最小项。
dist[start] = 0; pq.push({0, start}); // 初始只知道起点的距离。
while (!pq.empty()) {
    auto [du, u] = pq.top(); pq.pop(); // 取一份历史候选，并非直接信任它。
    if (du != dist[u]) continue; // 已被更短路径替代的堆项无需再扩展。
    for (auto [v, w] : adj[u]) {
        if (du + w < dist[v]) { // 用“到 u 的最短路 + 当前边”尝试改善。
            dist[v] = du + w; // 只接受严格改善，零权环不会绕出前驱环。
            parent[v] = u;
            pq.push({dist[v], v}); // 不删除旧候选，出堆时用上面的检查过滤。
        }
    }
}`};
