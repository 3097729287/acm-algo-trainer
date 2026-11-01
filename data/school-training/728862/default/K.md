## K. Directing Edges

### 题意

给定混合图，固定有向边不能改，将全部无向边定向，使最终图没有有向环。不存在则输出 `NO`，否则输出全部边方向。各组顶点数与边数总和分别不超过 $2\times10^5$。

### 从零讲：嵌套 vector 与 queue

**邻接表与队列。** `vector<vector<int>> graph(n)` 为每个点保存一份出边列表，遍历 `graph[u]` 就是在枚举其后继。总存储量为 $O(n+m)$。`std::queue<int>` 用 `push` 加入队尾，用 `q.front();`、`q.pop();` 读取并移除队首；必须先用 `q.empty();` 判空。这些队列操作均为 $O(1)$。

### 思路

只对已经有方向的边做拓扑排序。若这些边本来就有环，答案为 `NO`；否则得到每个顶点在拓扑序中的位置，将所有无向边从位置靠前的顶点指向靠后的顶点。

![固定边与无向边统一沿同一拓扑序向前](assets/k-order.svg)

固定边已沿拓扑序向后，新增方向也这样选，所以每走一条边，位置都严格增加，不可能回到起点，最终一定无环。Kahn 算法每条有向边处理一次，总时间 $O(n+m)$，空间 $O(n+m)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Edge { int type, u, v; };

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        cin >> n >> m;
        vector<Edge> edges(m);
        vector<vector<int>> graph(n);
        vector<int> indegree(n, 0);
        for (Edge &e : edges) {
            cin >> e.type >> e.u >> e.v;
            --e.u; --e.v;
            // 无向边尚未定向，不能参与入度或判环。
            if (e.type == 1) {
                graph[e.u].push_back(e.v);
                ++indegree[e.v];
            }
        }
        queue<int> q;
        for (int u = 0; u < n; ++u) if (indegree[u] == 0) q.push(u);
        vector<int> position(n, -1);
        int count = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            position[u] = count++;
            for (int v : graph[u]) if (--indegree[v] == 0) q.push(v);
        }
        if (count != n) { cout << "NO\n"; continue; }
        cout << "YES\n";
        for (Edge e : edges) {
            // 所有新增方向都沿拓扑序向后，因此不可能绕回起点。
            if (e.type == 0 && position[e.u] > position[e.v]) swap(e.u, e.v);
            cout << e.u + 1 << ' ' << e.v + 1 << '\n';
        }
    }
}
```

### 易错点

无向边不参与拓扑入度；已有方向不能改变；非连通图要把所有入度零顶点加入初始队列。
