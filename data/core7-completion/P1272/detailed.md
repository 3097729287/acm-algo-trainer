## P1272 重建道路

原题：[P1272](https://www.luogu.com.cn/problem/P1272)

### 从问题到算法

目标连通块有唯一最高点 u。若不保留某个孩子子树，切断 u 与该孩子的边；若保留，就必须接纳一个包含孩子根的连通块。

初始 dp[u][1]=孩子数，相当于暂时切断所有孩子边。合并孩子 v 的 j 个点时，用 dp[u][s]+dp[v][j]−1 更新 dp[u][s+j]，减一是恢复预先切掉的 u—v。保持原状态则表示继续切掉该子树。

全部合并后，若 u 不是全树根，还要切断其父边，才能使这个块独立。因此答案是所有 u 的 dp[u][P]+[u非根] 最小值。每个合法块都以它的最高点被枚举，且每条边的去留被准确计费。

### 复杂度

时间 O(NP²)，空间 O(NP)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, P;
    cin >> n >> P;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        g[u - 1].push_back(v - 1);
    }
    const int INF = 1000000;
    vector<vector<int>> dp(n, vector<int>(P + 1, INF));
    vector<int> size(n);
    function<void(int)> dfs = [&](int v) {
        size[v] = 1;
        dp[v][1] = g[v].size();
        for (int u : g[v]) {
            dfs(u);
            vector<int> next = dp[v];
            for (int s = 1; s <= min(P, size[v]); s++)
                for (int j = 1; j <= min(size[u], P - s); j++)
                    next[s + j] = min(next[s + j], dp[v][s] + dp[u][j] - 1);
            dp[v].swap(next);
            size[v] += size[u];
        }
    };
    dfs(0);
    int ans = INF;
    for (int v = 0; v < n; v++)
        ans = min(ans, dp[v][P] + (v != 0));
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

块必须含状态根；接纳孩子减掉一条预切边；非根答案补父边。
