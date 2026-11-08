## CF659E New Reform

原题：[CF659E](https://www.luogu.com.cn/problem/CF659E)

### 从问题到算法

目标是尽量减少入度为零的顶点。一个有 v 个点的树只有 v−1 条边，全部顶点入度之和也是 v−1，不可能人人入度至少为一，因此至少有一个零入度点。任选根，所有边由根指向孩子，恰好只有根为零，达到下界。

如果连通分量含环，把一个环按环方向定向；环上每点已有入边。再从环向未覆盖的点做搜索，把搜索树边由内向外定向，每个新点也得到一条入边，其余边任意定向即可。此时贡献为零。

所以只需遍历无向连通分量，统计点数 v 和邻接表总长度的一半 e。连通无向图满足 e=v−1 当且仅当它是树。孤立点同样是一棵树，要贡献一。

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
