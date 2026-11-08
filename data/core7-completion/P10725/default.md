## P10725 最远点对

原题：[P10725](https://www.luogu.com.cn/problem/P10725)

### 思路

每个点分别记录子树内到黑点、白点的最长向下距离。合并孩子时，把已有白分支与孩子黑分支、已有黑分支与孩子白分支相接，更新答案。

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
