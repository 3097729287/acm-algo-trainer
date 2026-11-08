## CF1245D Shichikuji and Power Grid

原题：[CF1245D](https://www.luogu.com.cn/problem/CF1245D)

### 思路

增加虚拟电源 0，连接城市 i 的费用为建站费 c_i，城市间边权为曼哈顿距离乘 (k_i+k_j)。对这张隐式完全图做 Prim，同时记录每个城市是建站还是接线。

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
    vector<long long> x(n), y(n), c(n), k(n), distance;
    for (int i = 0; i < n; i++)
        cin >> x[i] >> y[i];
    for (auto &v : c)
        cin >> v;
    for (auto &v : k)
        cin >> v;
    distance = c;
    vector<int> from(n, -1), stations;
    vector<pair<int, int>> wires;
    vector<char> used(n);
    long long answer = 0;
    for (int step = 0; step < n; step++) {
        int v = -1;
        for (int i = 0; i < n; i++)
            if (!used[i] && (v < 0 || distance[i] < distance[v]))
                v = i;
        used[v] = 1;
        answer += distance[v];
        if (from[v] < 0)
            stations.push_back(v + 1);
        else
            wires.push_back({from[v] + 1, v + 1});
        for (int u = 0; u < n; u++)
            if (!used[u]) {
                long long cost = (llabs(x[u] - x[v]) + llabs(y[u] - y[v])) * (k[u] + k[v]);
                if (cost < distance[u]) {
                    distance[u] = cost;
                    from[u] = v;
                }
            }
    }
    cout << answer << '\n' << stations.size() << '\n';
    for (int v : stations)
        cout << v << ' ';
    cout << '\n' << wires.size() << '\n';
    for (auto [a, b] : wires)
        cout << a << ' ' << b << '\n';

    return 0;
}
```

### 实现提醒

允许建多座电站；线路单价是两城市 k 之和；记录来源并输出实际方案。
