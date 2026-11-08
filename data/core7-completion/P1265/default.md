## P1265 公路修建

原题：[P1265](https://www.luogu.com.cn/problem/P1265)

### 思路

每两个城镇之间都能修路，权值为欧氏距离。无需生成全部边，用 Prim 保存每个未加入城镇到当前树的最短距离，逐个加入最近者。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long double> x(n), y(n), distance(n, numeric_limits<long double>::infinity());
    for (int i = 0; i < n; i++)
        cin >> x[i] >> y[i];
    vector<char> used(n);
    distance[0] = 0;
    long double ans = 0;
    for (int step = 0; step < n; step++) {
        int v = -1;
        for (int i = 0; i < n; i++)
            if (!used[i] && (v < 0 || distance[i] < distance[v]))
                v = i;
        used[v] = 1;
        ans += sqrt(distance[v]);
        for (int u = 0; u < n; u++)
            if (!used[u])
                distance[u] =
                    min(distance[u], (x[u] - x[v]) * (x[u] - x[v]) + (y[u] - y[v]) * (y[u] - y[v]));
    }
    cout << fixed << setprecision(2) << ans << '\n';

    return 0;
}
```

### 实现提醒

距离比较可用平方；加入时才开方；答案保留两位小数。
