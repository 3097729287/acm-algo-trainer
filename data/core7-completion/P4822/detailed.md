## P4822 冻结

原题：[P4822](https://www.luogu.com.cn/problem/P4822)

### 从问题到算法

同一座城市已经用掉多少卡，会影响后续可选择的路线，因此不能只为城市保存一个距离。把状态写为 (城市,used)，used 从零到 K。

每条原边产生两种转移：不用卡走到 (邻点,used)，花费 w；若 used<K，使用一张卡走到 (邻点,used+1)，花费 w/2。每条路最多用一张卡，恰好对应一次转移最多跨一层。所有费用非负，可以用 Dijkstra。

题目不要求用完卡，所以答案取终点所有层的最小值。原边保证偶数，除二是精确整数。

### 复杂度

时间 O((nK+mK) log(nK))，空间 O(nK+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, K;
    cin >> n >> m >> K;
    vector<vector<pair<int, int>>> g(n);
    while (m--) {
        int u, v, w;
        cin >> u >> v >> w;
        u--;
        v--;
        g[u].push_back({v, w});
        g[v].push_back({u, w});
    }
    const long long INF = 1LL << 60;
    vector<long long> d(n * (K + 1), INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[0] = 0;
    q.push({0, 0});
    while (!q.empty()) {
        auto [dist, state] = q.top();
        q.pop();
        if (dist != d[state])
            continue;
        int used = state / n, v = state % n;
        for (auto [u, w] : g[v])
            for (int take = 0; take <= 1 && used + take <= K; take++) {
                int next = (used + take) * n + u;
                long long nd = dist + (take ? w / 2 : w);
                if (nd < d[next]) {
                    d[next] = nd;
                    q.push({nd, next});
                }
            }
    }
    long long ans = INF;
    for (int k = 0; k <= K; k++)
        ans = min(ans, d[k * n + n - 1]);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

同一条路不能连续叠卡；允许少用卡；道路双向。
