## CF685B Kay and Snowflake

原题：[CF685B](https://www.luogu.com.cn/problem/CF685B)

### 思路

求子树大小后，若最大孩子不超过子树的一半，当前根就是重心；否则从这个大孩子的重心开始，向上移动到祖先侧大小不超过一半的位置。每个子树答案预先保存。

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
