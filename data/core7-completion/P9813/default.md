## P9813 Convex Hull

原题：[P9813](https://www.luogu.com.cn/problem/P9813)

### 思路

把状态设为顶点和累计损伤，只扩展新损伤严格小于 k 的边。按时间跑 Dijkstra，取终点所有合法损伤状态的最短时间。

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
