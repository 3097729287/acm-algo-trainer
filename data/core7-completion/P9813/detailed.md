## P9813 Convex Hull

原题：[P9813](https://www.luogu.com.cn/problem/P9813)

### 从问题到算法

最快到达某点的路线可能损伤很高，后面无法继续，因此每点需要分别保留不同损伤值的最佳时间。k 不超过二百，直接建立 n·k 个状态。

从 (v,h) 沿边走到 (u,h+损伤)，仅当新损伤<k 时允许；距离增加边的时间。边时间为正，可以使用 Dijkstra。任意合法原路线与状态图路线一一对应，最终对终点所有损伤取最小即可。

损伤为零的边同样合法，不能要求损伤每步严格上升。没有终点状态可达时输出 −1。

### 复杂度

时间 O((nk+mk) log(nk))，空间 O(nk+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int K, n, m;
    cin >> K >> n >> m;
    vector<vector<array<int, 3>>> g(n);
    while (m--) {
        int u, v, t, h;
        cin >> u >> v >> t >> h;
        u--;
        v--;
        g[u].push_back({v, t, h});
        g[v].push_back({u, t, h});
    }
    int s, t;
    cin >> s >> t;
    s--;
    t--;
    const long long INF = 1LL << 60;
    vector<long long> d(n * K, INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[s] = 0;
    q.push({0, s});
    while (!q.empty()) {
        auto [dist, state] = q.top();
        q.pop();
        if (d[state] != dist)
            continue;
        int h = state / n, v = state % n;
        for (auto [u, cost, damage] : g[v])
            if (h + damage < K) {
                int next = (h + damage) * n + u;
                if (d[next] > dist + cost) {
                    d[next] = dist + cost;
                    q.push({d[next], next});
                }
            }
    }
    long long ans = INF;
    for (int h = 0; h < K; h++)
        ans = min(ans, d[h * n + t]);
    cout << (ans == INF ? -1 : ans) << '\n';

    return 0;
}
```

### 实现提醒

限制是严格小于 k；道路双向；零损伤边保留。
