## P4551 最长异或路径

原题：[P4551](https://www.luogu.com.cn/problem/P4551)

### 从问题到算法

两条根路径的公共部分在异或中出现两次，会相互抵消，剩下的正是 u 到 v 的路径。因此树上路径问题变成从全部根路径异或值中选两个数，使异或最大。

从最高二进制位开始比较大小。查询值这一位为 b 时，若字典树存在 1−b 分支，就使结果当前位为一；高位一的收益大于所有低位之和，所以这是安全的贪心选择。不存在反位才走同位。

先用显式遍历计算 d，再插入并查询所有数。允许与自己配对得到零，不会使最大值变错；只有一个顶点时答案也为零。

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
