# 最短路：从一步到达转向累计费用

路径费用是沿途边权之和。无权图的 BFS 按边数分层；边权不同时，先到达的路线不一定更便宜。最短路算法维护每个顶点目前已知的最小费用 `dist`，用已知路径尝试改善邻居，这一步叫松弛。

图有边 $s\to a$ 权五、$s\to b$ 权一、$b\to a$ 权二。直接到 $a$ 费用五，通过 $b$ 仅需三。所以不能第一次见到 $a$ 就永远固定为五。

![先发现费用五，再通过费用一加二改进为三](assets/shortest-path.svg)

## 非负边权的 Dijkstra

起点距离零，其余为不可达。每次从小根堆取出当前最小的距离，若不是过期项，就松弛所有出边。非负边权保证尚未处理的更远顶点不可能绕出一条更便宜的路来推翻当前最小者。

```cpp
using State = pair<long long,int>;
priority_queue<State, vector<State>, greater<State>> heap;
dist[start] = 0; heap.push({0, start});
while (!heap.empty()) {
    auto [d, u] = heap.top(); heap.pop();
    if (d != dist[u]) continue;
    for (auto [v, weight] : graph[u]) {
        if (d + weight < dist[v]) {
            dist[v] = d + weight;
            heap.push({dist[v], v});
        }
    }
}
```

此实现可能为一个顶点保存多份堆项，更新后旧项仍在堆中，所以须检查是否过期。按实际入堆的边数，时间 $O((n+m)\log(n+m))$，空间 $O(n+m)$；常见简单图也写成 $O((n+m)\log n)$。距离和加边权要避免溢出。

若边权只为零或一，可用双端队列：零权改善放前端，一权改善放后端，称 0-1 BFS，正确实现可达 $O(n+m)$。负权图不能套非负贪心理由；Bellman-Ford 通过多轮松弛求解并检测可达负环，最坏 $O(nm)$。差分约束 $x_v\le x_u+w$ 可表示为边 $u\to v$ 权 $w$，但求解方向、超级源和负环含义要按约束目标解释。

状态不一定只是原图顶点。若后续费用还依赖钥匙、颜色或次数，应把这些信息并入状态；两条到同一顶点的路径未必能互相替代。
