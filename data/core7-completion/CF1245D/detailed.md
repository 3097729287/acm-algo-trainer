## CF1245D Shichikuji and Power Grid

原题：[CF1245D](https://www.luogu.com.cn/problem/CF1245D)

### 从问题到算法

一个合法供电网络中，每座城市都必须通过线路连到某座电站。增加虚拟点 0，把建站看作连接 0 的一条边后，供电要求就等价于所有城市与 0 连通，目标为最小生成树。

初始化每个城市的最佳费用为它自己的建站费、来源为 0，表示已经把虚拟点加入树。每轮选费用最小的未选城市，累加费用并记录它的来源；随后用它到其它城市的线路费用尝试改进。

来源为 0 的城市需要建站，其余来源记录一条电线。Prim 的割性质保证总价最小。n<=2000，平方扫描即可，不必储存全部城市边；费用乘积与总额用 long long。

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
