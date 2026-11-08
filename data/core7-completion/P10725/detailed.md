## P10725 最远点对

原题：[P10725](https://www.luogu.com.cn/problem/P10725)

### 从问题到算法

任意一条树路径有唯一最高点。只要在这个点处理连接两条不同分支的路径，就能覆盖所有候选。

令 down[u][c] 是 u 到子树中颜色 c 的最远距离，不存在则为负无穷。当前点自身给对应颜色距离零。逐个合并孩子 v：用 down[u][0]+down[v][1]+1 和 down[u][1]+down[v][0]+1 更新答案，再将孩子距离加一并入 down[u]。

必须先计算跨分支贡献再合并，避免把同一个孩子中的两条路线错误拼成经过 u 的路径。孩子内部的最优路径已经在处理孩子时计算。按迭代遍历顺序逆序处理，可避免长链递归溢出。

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
    vector<int> a(n);
    for (int &x : a)
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
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    const int NEG = -1000000000;
    vector<array<int, 2>> down(n, {NEG, NEG});
    int ans = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        down[v][a[v]] = 0;
        for (int u : g[v])
            if (parent[u] == v) {
                ans = max({ans, down[v][0] + down[u][1] + 1, down[v][1] + down[u][0] + 1});
                for (int c = 0; c < 2; c++)
                    down[v][c] = max(down[v][c], down[u][c] + 1);
            }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

两端颜色不同；距离按边数；不存在颜色用负无穷。
