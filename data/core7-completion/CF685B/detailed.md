## CF685B Kay and Snowflake

原题：[CF685B](https://www.luogu.com.cn/problem/CF685B)

### 从问题到算法

删去 u 后，若每个孩子子树都不超过 size[u]/2，u 就满足重心定义。否则只有一个孩子 h 超过一半，重心必在 h 子树中。

已知 h 子树的重心 c，它向下的各部分不超过 size[h]/2，也就不超过 size[u]/2。扩大到 u 子树后，唯一可能过大的部分是祖先侧，大小为 size[u]−size[c]。当这个值超过一半时，将 c 移到父亲。移动时原来的下方 c 部分小于一半，其它孩子也不会超过原最大孩子，所以新的唯一潜在问题仍是祖先侧。

这样向上走到第一次满足条件即得到重心。后序处理全部子树，再按询问直接输出保存结点。子树可能有两个重心，任意一个都合法。

### 复杂度

预处理 O(n log n) 的保守上界，每问 O(1)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<int> parent(n), size(n, 1), heavy(n, -1), center(n);
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        cin >> parent[i];
        parent[i]--;
        g[parent[i]].push_back(i);
    }
    vector<int> order = {0};
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            order.push_back(u);
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        for (int u : g[v]) {
            size[v] += size[u];
            if (heavy[v] < 0 || size[u] > size[heavy[v]])
                heavy[v] = u;
        }
        int h = heavy[v];
        if (h < 0 || size[h] * 2 <= size[v])
            center[v] = v;
        else {
            int c = center[h];
            while ((size[v] - size[c]) * 2 > size[v])
                c = parent[c];
            center[v] = c;
        }
    }
    while (q--) {
        int v;
        cin >> v;
        cout << center[v - 1] + 1 << '\n';
    }

    return 0;
}
```

### 实现提醒

子树大小包括自己；只沿过半孩子进入；两重心均可。
