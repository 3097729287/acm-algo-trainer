## UVA1222 Bribing FIPA

原题：[UVA1222](https://www.luogu.com.cn/problem/UVA1222)

### 从问题到算法

统属关系无环且每国至多一个上级，因此形成森林。为所有根增加虚拟父亲零，虚拟根不能贿赂，也不提供选票。原题关系可核对[原题 PDF](https://onlinejudge.org/external/12/1222.pdf)。

对国家 u，先把孩子子树的“恰好取得 j 票的最小费用”用背包卷积合并；这表示不直接贿赂 u，只从后代购买。随后将整棵 u 子树的票数状态与 cost[u] 取较小值，表示贿赂 u 后无需再贿赂任何后代。

这两类方案覆盖所有最优选择：一旦贿赂 u，重复购买后代不会增加票数；若不贿赂 u，孩子之间完全独立。最终在虚拟根上对票数≥m 的状态取最小。名字可能先在他国列表中出现，用映射统一编号，不能只按出现行号直接引用。

### 复杂度

时间 O(n²)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string line;
    while (getline(cin, line)) {
        if (line == "#")
            break;
        if (line.empty())
            continue;
        istringstream header(line);
        int n, m;
        header >> n >> m;
        map<string, int> ids;
        int used = 0;
        auto get = [&](const string &s) {
            auto it = ids.find(s);
            if (it != ids.end())
                return it->second;
            return ids[s] = ++used;
        };
        vector<vector<int>> g(n + 1);
        vector<int> parent(n + 1), size(n + 1);
        vector<long long> cost(n + 1);
        for (int i = 0; i < n; i++) {
            getline(cin, line);
            istringstream in(line);
            string name;
            long long value;
            in >> name >> value;
            int u = get(name);
            cost[u] = value;
            while (in >> name) {
                int v = get(name);
                g[u].push_back(v);
                parent[v] = u;
            }
        }
        for (int i = 1; i <= n; i++)
            if (!parent[i])
                g[0].push_back(i);
        vector<int> order = {0};
        for (int i = 0; i < (int)order.size(); i++)
            for (int u : g[order[i]])
                order.push_back(u);
        const long long INF = 1LL << 60;
        vector<vector<long long>> dp(n + 1);
        for (int i = n; i >= 0; i--) {
            int v = order[i];
            dp[v] = {0};
            for (int u : g[v]) {
                vector<long long> next(size[v] + size[u] + 1, INF);
                for (int a = 0; a <= size[v]; a++)
                    for (int b = 0; b <= size[u]; b++)
                        next[a + b] = min(next[a + b], dp[v][a] + dp[u][b]);
                size[v] += size[u];
                dp[v].swap(next);
            }
            if (v) {
                size[v]++;
                dp[v].resize(size[v] + 1, INF);
                dp[v][size[v]] = min(dp[v][size[v]], cost[v]);
            }
        }
        cout << *min_element(dp[0].begin() + m, dp[0].end()) << '\n';
    }

    return 0;
}
```

### 实现提醒

要求至少 m 票；虚拟根不计票且不能购买；国家名称按整行解析。
