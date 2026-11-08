## P6833 雷雨

原题：[P6833](https://www.luogu.com.cn/problem/P6833)

### 思路

分别从 O、A、B 跑三次带点权的 Dijkstra，距离包含起终点权。枚举分叉格 v，答案为 min(dO[v]+dA[v]+dB[v]−2R[v])。

### 复杂度

时间 O(nm log(nm))，空间 O(nm)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, a, b, c;
    cin >> n >> m >> a >> b >> c;
    int N = n * m;
    vector<long long> w(N);
    for (auto &x : w)
        cin >> x;
    auto dijkstra = [&](int s) {
        const long long INF = 1LL << 62;
        vector<long long> d(N, INF);
        priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                       greater<pair<long long, int>>>
            q;
        d[s] = w[s];
        q.push({d[s], s});
        while (!q.empty()) {
            auto [dist, v] = q.top();
            q.pop();
            if (d[v] != dist)
                continue;
            int x = v / m, y = v % m;
            for (int u :
                 {x ? v - m : -1, x + 1 < n ? v + m : -1, y ? v - 1 : -1, y + 1 < m ? v + 1 : -1})
                if (u >= 0 && d[u] > dist + w[u]) {
                    d[u] = dist + w[u];
                    q.push({d[u], u});
                }
        }
        return d;
    };
    auto x = dijkstra(a - 1), y = dijkstra((n - 1) * m + b - 1), z = dijkstra((n - 1) * m + c - 1);
    long long ans = LLONG_MAX;
    for (int v = 0; v < N; v++)
        ans = min(ans, x[v] + y[v] + z[v] - 2 * w[v]);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

三份距离都含起点；汇合点减两次权；允许零权格；答案用 long long。
