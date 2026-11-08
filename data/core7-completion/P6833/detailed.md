## P6833 雷雨

原题：[P6833](https://www.luogu.com.cn/problem/P6833)

### 从问题到算法

两条路径的并集可以去掉环，得到连接 O、A、B 的树。在这棵树中，存在一个汇合点 v，使到三个端点的三条分支内部互不相交。最优树的分支费用至少是对应最短路距离，三个距离都包含 v，故要减去两次 R[v]。这给出某个候选值不大于最优费用。

反过来，对任意 v 取三条最短路，它们的并集连通且覆盖三个端点。因为所有点权非负，并集费用不会超过三个距离之和减去重复计算的两次 R[v]，所以最优费用又不大于每个候选值。上下界一致，公式成立，即使最短路额外重叠也不影响证明。

移动到邻格的代价取邻格点权，源距离初始化为源点权。数据规模要求六十四位距离。

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
