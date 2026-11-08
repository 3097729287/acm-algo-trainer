## P4551 最长异或路径

原题：[P4551](https://www.luogu.com.cn/problem/P4551)

### 思路

任选根，记录根到每点的边权异或 d。两点路径异或为 d[u] xor d[v]。把所有 d 插入二进制字典树，逐位优先走相反位，求最大异或值。

### 复杂度

时间 O(n log W)，空间 O(n log W)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<pair<int, int>>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b, w;
        cin >> a >> b >> w;
        a--;
        b--;
        g[a].push_back({b, w});
        g[b].push_back({a, w});
    }
    vector<int> d(n), parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < (int)order.size(); i++) {
        int v = order[i];
        for (auto [u, w] : g[v])
            if (u != parent[v]) {
                parent[u] = v;
                d[u] = d[v] ^ w;
                order.push_back(u);
            }
    }
    vector<array<int, 2>> t(1);
    for (int x : d) {
        int v = 0;
        for (int b = 30; b >= 0; b--) {
            int bit = (x >> b) & 1;
            if (!t[v][bit]) {
                t[v][bit] = t.size();
                t.push_back({0, 0});
            }
            v = t[v][bit];
        }
    }
    int ans = 0;
    for (int x : d) {
        int v = 0, value = 0;
        for (int b = 30; b >= 0; b--) {
            int bit = (x >> b) & 1;
            if (t[v][bit ^ 1]) {
                value |= 1 << b;
                v = t[v][bit ^ 1];
            } else
                v = t[v][bit];
        }
        ans = max(ans, value);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

先求根路径异或而非距离和；高位优先；非递归遍历避免长链栈溢出。
