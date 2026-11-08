## CF659E New Reform

原题：[CF659E](https://www.luogu.com.cn/problem/CF659E)

### 思路

每个连通分量单独考虑。树无论怎样定向都至少留下一个入度为 0 的点；含环分量可以沿环定向，再由环向外扩展，使所有点入度至少为 1。答案是树形连通分量个数。

### 复杂度

时间 O(n+m)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> g(n);
    while (m--) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    vector<char> seen(n);
    int ans = 0;
    for (int s = 0; s < n; s++)
        if (!seen[s]) {
            long long edges = 0;
            int vertices = 0;
            vector<int> st = {s};
            seen[s] = 1;
            while (!st.empty()) {
                int v = st.back();
                st.pop_back();
                vertices++;
                edges += g[v].size();
                for (int u : g[v])
                    if (!seen[u]) {
                        seen[u] = 1;
                        st.push_back(u);
                    }
            }
            ans += edges / 2 == vertices - 1;
        }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

无向边在邻接表中出现两次；孤立点也要统计。
