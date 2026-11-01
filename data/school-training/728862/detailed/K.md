## K. Directing Edges

### 题意

给定混合图，固定有向边不能改，将全部无向边定向，使最终图没有有向环。不存在则输出 `NO`，否则输出全部边方向。各组顶点数与边数总和分别不超过 $2\times10^5$。

### 从零讲：嵌套 vector 与 queue

**邻接表与队列。** `vector<vector<int>> graph(n)` 为每个点保存一份出边列表，遍历 `graph[u]` 就是在枚举其后继。总存储量为 $O(n+m)$。`std::queue<int>` 用 `push` 加入队尾，用 `q.front();`、`q.pop();` 读取并移除队首；必须先用 `q.empty();` 判空。这些队列操作均为 $O(1)$。

### 思路

不能逐条随意给无向边定向，因为局部看没有问题的选择，合起来可能形成环。先给所有顶点安排一个统一的先后顺序，要求每条固定有向边都从前指向后；这种顺序称为拓扑序。

![先按固定边排顺序，再处理待定边](assets/k-order.svg)

图中固定边为 $1\to3$、$2\to3$。可取顺序 $1,2,3,4$，再把待定边 $1\! -\!2$ 定为 $1\to2$，把 $3\! -\!4$ 定为 $3\to4$。如果某条边的原输入写成 $4,3$，仍应按拓扑位置交换后输出，不能按输入编号猜方向。

#### 只在固定边上做拓扑排序

入度是指向顶点的边数。没有任何前置要求的顶点，也就是当前入度为零的顶点，可以先放入序列。Kahn 算法用队列维护这些点：取出一个顶点，把它的所有出边删去，相邻顶点入度减少；新变成零的点再入队。

这里只统计固定有向边，无向边还没有方向，不能给它增加入度。若处理了全部 $n$ 个顶点，就得到合法顺序；若还有点剩下，则它们各有剩余前驱，沿前驱不断走必会重复顶点，说明固定边已有有向环。这些方向无法修改，答案必为 `NO`。

#### 为什么沿顺序定向就够了

若固定边无环，将每条待定边从拓扑位置较小端指向较大端。所有边都让位置严格增加；而有向环要求最终回到起点，也就是位置回到原值，二者矛盾。因此这个构造对整张图成立，也适用于非连通图。

代码保存全部原边用于最后输出，但只为固定边建立邻接表。每组都重新创建入度、队列和拓扑位置，防止上一组数据污染。时间 $O(n+m)$，空间 $O(n+m)$；多组总规模受题面给出的总和限制。

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
