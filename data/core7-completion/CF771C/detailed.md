## CF771C Bear and Tree Jumps

原题：[CF771C](https://www.luogu.com.cn/problem/CF771C)

### 从问题到算法

ceil(d/k)=(d+(k−d%k)%k)/k。第一项所有距离之和可按边计算：一条边切开大小为 s、n−s 两部分，恰有 s(n−s) 个无序点对使用它。

第二项只与距离余数有关。cnt[u][r] 记录 u 子树中距 u 余数为 r 的点数。合并孩子时，孩子的余数先加一，和已有分支余数 r 配对，路径经过 u，所以总余数是两者相加模 k；按所需补齐量乘点对数量累计。

每对点在其 LCA 合并两个分支时被统计一次。当前点自身放在余数零状态，覆盖一个端点就是祖先的情形。k≤5，平方余数枚举很小。

### 复杂度

时间 O(nk²)，空间 O(nk)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    vector<int> parent(n, -1), order = {0}, size(n, 1);
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    vector<array<long long, 5>> cnt(n);
    long long distanceSum = 0, padding = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        cnt[v][0] = 1;
        for (int u : g[v])
            if (parent[u] == v) {
                for (int a = 0; a < k; a++)
                    for (int b = 0; b < k; b++)
                        padding += cnt[v][a] * cnt[u][b] * ((k - (a + b + 1) % k) % k);
                for (int b = 0; b < k; b++)
                    cnt[v][(b + 1) % k] += cnt[u][b];
                size[v] += size[u];
            }
        if (v)
            distanceSum += 1LL * size[v] * (n - size[v]);
    }
    cout << (distanceSum + padding) / k << '\n';

    return 0;
}
```

### 实现提醒

点对无序，只合并不同已处理分支；余数零无需补；最终总和整除 k。
