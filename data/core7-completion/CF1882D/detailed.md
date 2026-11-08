## CF1882D Tree XOR

原题：[CF1882D](https://www.luogu.com.cn/problem/CF1882D)

### 从问题到算法

操作可使一整棵子树的数值统一异或，沿边两侧的差异代价只由端点的异或值决定。固定根以后，这条边的代价影响子树内每个点，因此贡献为边权 w=a[u] xor a[v] 乘子树大小。各边贡献相加得到根的总代价。

任选 1 为根，用遍历顺序的倒序计算子树大小，并求 Σw·size。把根从父 u 移到子 v 时，只有这条边的两侧归属改变：原来乘 size[v]，现在乘 n−size[v]，其余边的分割方向不变。所以 answer[v]=answer[u]+w(n−2size[v])。

按父先子的顺序传播答案，每条边只处理常数次。所有乘积与答案用 long long，避免大型星形树溢出。

三点链的点值为 1、2、3，两条边权为 3 与 1。根从 1 移到 2，再移到 3，总代价依次为 7、4、5；动图中仅跨过的那条边改变乘上的点数。

![换根时只有跨过的这条边改变贡献](assets/reroot-xor.svg)

### 复杂度

每组时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<long long> a(n), ans(n);
        for (auto &x : a)
            cin >> x;
        vector<vector<int>> g(n);
        for (int i = 1; i < n; i++) {
            int u, v;
            cin >> u >> v;
            u--;
            v--;
            g[u].push_back(v);
            g[v].push_back(u);
        }
        vector<int> parent(n, -1), size(n, 1), order = {0};
        parent[0] = 0;
        for (int i = 0; i < n; i++)
            for (int u : g[order[i]])
                if (u != parent[order[i]]) {
                    parent[u] = order[i];
                    order.push_back(u);
                }
        for (int i = n - 1; i > 0; i--) {
            int v = order[i], p = parent[v];
            size[p] += size[v];
            ans[0] += (a[v] ^ a[p]) * size[v];
        }
        for (int i = 1; i < n; i++) {
            int v = order[i], p = parent[v];
            ans[v] = ans[p] + (a[v] ^ a[p]) * (n - 2LL * size[v]);
        }
        for (long long x : ans)
            cout << x << ' ';
        cout << '\n';
    }

    return 0;
}
```

### 实现提醒

边权是端点值异或；换根差为 n−2size；使用六十四位。
