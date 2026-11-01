## J. Shichikuji and Power Grid

### 题意

有至多 $2000$ 座城市。城市 $i$ 建站费用为 $c_i$，连接 $i,j$ 的费用为曼哈顿距离乘 $k_i+k_j$。求全城供电的最小费用并输出建站与连线方案。

### 从零讲：vector 与 pair

**动态数组与二元组。** `vector<long long> best = c` 复制建站费用，之后改 `best` 不会改 原数组。`std::pair<int,int>` 把一条线的两个城市编号放在一起，`edge.first`、`edge.second` 分别读取两端；`push_back` 在尾部追加，均摊 $O(1)$，增容时可能使原引用失效。`for (auto edge : wires)` 根据容器元素推断为二元组的值副本。`abs` 取绝对值，传入 `long long` 差值以使用对应重载。

### 思路

增加虚拟顶点 $0$：边 $0\! -\! i$ 的费用为 $c_i$，表示城市 $i$ 建电站；普通城市间边的费用为

$$w(i,j)=(|x_i-x_j|+|y_i-y_j|)(k_i+k_j).$$

![把建站与连线放入同一张图](assets/j-power.svg)

所有城市有电，等价于在新图中都与 $0$ 连通。取最小生成树即可：删掉虚拟点后，连接过虚拟点的城市建站，普通树边就是电线。

城市间是稠密图，用 $O(n^2)$ 的 Prim 算法，按需计算距离，无需保存所有边。初始 `best[i]=c[i]`，每次选最小的未加入城市，并用它更新其他城市。记录来源为虚拟点还是城市，即可恢复方案。时间 $O(n^2)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
using ll = long long;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<ll> x(n), y(n), c(n), k(n);
    for (int i = 0; i < n; ++i) cin >> x[i] >> y[i];
    for (ll &v : c) cin >> v;
    for (ll &v : k) cin >> v;
    // 虚拟点零已加入：到城市 i 的初始最优边就是建站费用。
    vector<ll> best = c;
    vector<int> from(n, -1), stations;
    vector<pair<int, int>> wires;
    vector<bool> used(n, false);
    ll total = 0;
    for (int step = 0; step < n; ++step) {
        int u = -1;
        for (int i = 0; i < n; ++i) {
            if (!used[i] && (u == -1 || best[i] < best[u])) u = i;
        }
        used[u] = true;
        total += best[u];
        if (from[u] == -1) stations.push_back(u + 1);
        else wires.push_back({from[u] + 1, u + 1});
        for (int v = 0; v < n; ++v) {
            if (used[v]) continue;
            ll cost = (abs(x[u] - x[v]) + abs(y[u] - y[v])) * (k[u] + k[v]);
            if (cost < best[v]) {
                best[v] = cost;
                from[v] = u;
            }
        }
    }
    cout << total << '\n' << stations.size() << '\n';
    for (int v : stations) cout << v << ' ';
    cout << '\n' << wires.size() << '\n';
    for (auto edge : wires) cout << edge.first << ' ' << edge.second << '\n';
}
```

### 易错点

坐标允许重合；所有边权乘法使用 `long long`；输出建站清单和连线清单，城市编号从一开始。
