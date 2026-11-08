## P1850 换教室

原题：[P1850](https://www.luogu.com.cn/problem/P1850)

### 思路

Floyd 求教室间最短路，dp[天数][申请次数][当天是否申请] 维护最小期望路程。相邻两天按各自成功或失败的概率组合四种距离转移。

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
