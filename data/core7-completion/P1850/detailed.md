## P1850 换教室

原题：[P1850](https://www.luogu.com.cn/problem/P1850)

### 从问题到算法

每天是否申请必须预先决定，不能看到结果再改变后续计划。申请结果相互独立，所以给定相邻两天是否申请后，它们之间的期望距离固定，可作为 DP 边权。

某天不申请时原教室概率一；申请时新教室概率 p、原教室概率 1−p。前后两天共有最多四种组合，把最短距离乘概率后相加。dp 只需保留上一天是否申请，便足以确定本次转移代价。

从第一天开始，没有之前的路程，不申请状态费用零，若有申请额度，申请状态也为零但用掉一次额度。逐日转移，最后对不超过 m 次的全部状态取最小。先对道路做 Floyd，重边取最小值。

### 复杂度

时间 O(v³+nm)，空间 O(v²+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, v, e;
    cin >> n >> m >> v >> e;
    vector<int> c(n), d(n);
    vector<long double> p(n);
    for (int &x : c) {
        cin >> x;
        x--;
    }
    for (int &x : d) {
        cin >> x;
        x--;
    }
    for (auto &x : p)
        cin >> x;
    const long double INF = 1e80L;
    vector<vector<long double>> dist(v, vector<long double>(v, INF));
    for (int i = 0; i < v; i++)
        dist[i][i] = 0;
    while (e--) {
        int a, b;
        long double w;
        cin >> a >> b >> w;
        a--;
        b--;
        dist[a][b] = dist[b][a] = min(dist[a][b], w);
    }
    for (int k = 0; k < v; k++)
        for (int i = 0; i < v; i++)
            for (int j = 0; j < v; j++)
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]);
    vector<array<long double, 2>> dp(m + 1, {INF, INF});
    dp[0][0] = 0;
    if (m)
        dp[1][1] = 0;
    for (int day = 1; day < n; day++) {
        long double cost[2][2]{};
        for (int before = 0; before < 2; before++)
            for (int now = 0; now < 2; now++)
                for (int a = 0; a < 2; a++)
                    for (int b = 0; b < 2; b++) {
                        long double pa = before ? (a ? p[day - 1] : 1 - p[day - 1]) : (a ? 0 : 1),
                                    pb = now ? (b ? p[day] : 1 - p[day]) : (b ? 0 : 1);
                        cost[before][now] +=
                            pa * pb * dist[a ? d[day - 1] : c[day - 1]][b ? d[day] : c[day]];
                    }
        vector<array<long double, 2>> next(m + 1, {INF, INF});
        for (int used = 0; used <= m; used++)
            for (int before = 0; before < 2; before++)
                for (int now = 0; now < 2; now++)
                    if (used + now <= m)
                        next[used + now][now] =
                            min(next[used + now][now], dp[used][before] + cost[before][now]);
        dp.swap(next);
    }
    long double ans = INF;
    for (auto state : dp)
        ans = min({ans, state[0], state[1]});
    cout << fixed << setprecision(2) << ans << '\n';

    return 0;
}
```

### 实现提醒

申请决定不能依据随机结果；第一天也可申请；最多 m 次而非恰好。
