## J. Shichikuji and Power Grid

### 题意

有至多 $2000$ 座城市。城市 $i$ 建站费用为 $c_i$，连接 $i,j$ 的费用为曼哈顿距离乘 $k_i+k_j$。求全城供电的最小费用并输出建站与连线方案。

### 从零讲：vector 与 pair

**动态数组与二元组。** `vector<long long> best = c` 复制建站费用，之后改 `best` 不会改 原数组。`std::pair<int,int>` 把一条线的两个城市编号放在一起，`edge.first`、`edge.second` 分别读取两端；`push_back` 在尾部追加，均摊 $O(1)$，增容时可能使原引用失效。`for (auto edge : wires)` 根据容器元素推断为二元组的值副本。`abs` 取绝对值，传入 `long long` 差值以使用对应重载。

### 思路

难点在于统一“建电站”和“接电线”两种花钱方式。直接先选电站再铺线，可能错过更便宜的整体方案。引入一个只负责表示电源的虚拟顶点 $0$：选择 $0$ 到城市 $i$ 的边，就是花 $c_i$ 在这里建站。

![真实方案与虚拟图的逐项对应](assets/j-power.svg)

图使用第二组样例：城市 $2$ 建站花 $2$，城市 $1$ 接到 $2$ 花 $(1+1)(3+2)=10$，城市 $3$ 接到 $2$ 花 $(2+1)(2+3)=15$，总费用 $27$。虚拟图中恰好选三条边 $0\! -\!2$、$2\! -\!1$、$2\! -\!3$。

#### 为什么变成最小生成树

任意供电方案中，每个普通连通部分至少有一座电站；把每座电站与虚拟点相连，整张图就连通，费用不变。反过来，任何覆盖 $0,1,\ldots,n$ 的连通图，删去虚拟点后，每个部分必有城市曾与 $0$ 相连，在那里建站就能给该部分供电，费用也不变。

于是目标是最小费用的连通子图。边权均非负，连通图若有环，可以删去环上一条边而不破坏连通性、也不增加费用。最终可保留一棵生成树，最优费用就是最小生成树的费用。重复坐标产生零费用边，同样适用。

#### Prim 每一步维护什么

设 $S$ 为已经加入树的顶点，初始只有虚拟点。对每个未加入城市 $v$，`best[v]` 保存从 $S$ 接一条边到 $v$ 的最小费用，`from[v]` 保存这条边来自哪个城市；来源为虚拟点时记为 $-1$。初始只能从 $0$ 连出，所以 `best[v]=c[v]`。

![每轮选择跨越已选集合的最便宜边](assets/j-cut.svg)

每轮选择 `best` 最小的未选城市。这条边是所有跨越 $S$ 与外部的边里最便宜的一条。为什么能放心选？取任意一棵最优生成树，若它没有这条边，加进去会形成一个环；环上必有另一条跨越同一边界的边，替换掉它不会更贵，所以至少存在一棵最优树包含本轮选择。由此每轮都能保持扩展为最优解的可能。

新城市 $u$ 入树后，只有从 $u$ 连出的边可能改进其他城市的 `best`，逐一计算并更新即可。图有 $O(n^2)$ 条候选边，却无需把它们全部存起来。最后 `from[u]==-1` 的城市列入建站表，其余记录一条电线。

曼哈顿距离最多为 $2(10^6-1)$，两系数之和最多为 $2\times10^9$，单条候选边可以达到接近 $4\times10^{15}$，须在乘法前就使用 `long long`。最优费用不超过全建站的 $2\times10^{12}$。时间 $O(n^2)$，空间 $O(n)$。

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
