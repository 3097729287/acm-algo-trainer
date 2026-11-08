## P4284 概率充电器

原题：[P4284](https://www.luogu.com.cn/problem/P4284)

### 从问题到算法

边能传电与否、每点自身通电事件均独立。设 down[u] 为只考虑 u 子树时 u 不通电的概率，child v 这一路不能带电的概率为 (1−edgeP)+edgeP·down[v]。因此 down[u]=(1−自身概率) 乘全部孩子的这一因子。

再令 outside[u] 表示来自父侧的一切无法使 u 通电的概率，根为一。要向孩子 v 传递，先算 u 在去掉 v 子树后不通电的概率，即 outside[u]·(1−自身概率)·其余孩子因子；通过 u—v 边得到 outside[v]=(1−edgeP)+edgeP·该概率。

使用前后缀乘积排除一个孩子，不能用总乘积除以它的因子，因为因子可能为零。最后 down[u]outside[u] 为完全断电概率，利用期望线性性求和，不需要计算各点同时通电的联合分布。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<pair<int, long double>>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        long double p;
        cin >> a >> b >> p;
        a--;
        b--;
        p /= 100;
        g[a].push_back({b, p});
        g[b].push_back({a, p});
    }
    vector<long double> self(n), down(n), outside(n, 1), edge(n);
    for (auto &x : self) {
        cin >> x;
        x /= 100;
    }
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (auto [u, p] : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                edge[u] = p;
                order.push_back(u);
            }
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        down[v] = 1 - self[v];
        for (auto [u, p] : g[v])
            if (parent[u] == v)
                down[v] *= 1 - p + p * down[u];
    }
    long double ans = 0;
    for (int v : order) {
        ans += 1 - down[v] * outside[v];
        vector<int> children;
        vector<long double> factors;
        for (auto [u, p] : g[v])
            if (parent[u] == v) {
                children.push_back(u);
                factors.push_back(1 - p + p * down[u]);
            }
        int z = children.size();
        vector<long double> prefix(z + 1, 1), suffix(z + 1, 1);
        for (int i = 0; i < z; i++)
            prefix[i + 1] = prefix[i] * factors[i];
        for (int i = z - 1; i >= 0; i--)
            suffix[i] = suffix[i + 1] * factors[i];
        for (int i = 0; i < z; i++) {
            int u = children[i];
            long double no = outside[v] * (1 - self[v]) * prefix[i] * suffix[i + 1];
            outside[u] = 1 - edge[u] + edge[u] * no;
        }
    }
    cout << fixed << setprecision(6) << ans << '\n';

    return 0;
}
```

### 实现提醒

输入百分数除以一百；零因子用前后缀乘积；答案保留六位小数。
