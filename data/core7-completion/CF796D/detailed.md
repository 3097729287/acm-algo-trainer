## CF796D Police Stations

原题：[CF796D](https://www.luogu.com.cn/problem/CF796D)

### 从问题到算法

设有 s 个不同的警局城市。关闭 r 条树边会产生 r+1 个连通块，每块至少含一个警局，因此 r≤s−1。

从所有警局同时 BFS，第一次访问城市时继承前驱的归属。这个城市到所属警局的路线是原树最短路，题目保证最近警局距离不超过 d，所以归属区域内也满足距离限制。不同归属的端点之间的边关闭后，恰好得到 s 个连通区域，共关闭 s−1 条边，达到上界。

重复警局只放入队列一次。距离 d 无须参与扩展上限：完整多源 BFS 已分配给每个点最近的警局，原题保证的覆盖条件确保所有分配合法。

### 复杂度

时间 O(n+k)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k, d;
    cin >> n >> k >> d;
    vector<int> owner(n, -1), q;
    for (int i = 0; i < k; i++) {
        int p;
        cin >> p;
        p--;
        if (owner[p] < 0) {
            owner[p] = p;
            q.push_back(p);
        }
    }
    vector<vector<pair<int, int>>> g(n);
    vector<pair<int, int>> e;
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        e.push_back({a, b});
        g[a].push_back({b, i});
        g[b].push_back({a, i});
    }
    for (int i = 0; i < (int)q.size(); i++) {
        int v = q[i];
        for (auto [u, id] : g[v])
            if (owner[u] < 0) {
                owner[u] = owner[v];
                q.push_back(u);
            }
    }
    vector<int> cut;
    for (int i = 0; i < n - 1; i++)
        if (owner[e[i].first] != owner[e[i].second])
            cut.push_back(i + 1);
    cout << cut.size() << '\n';
    for (int i = 0; i < (int)cut.size(); i++)
        cout << cut[i] << (i + 1 == (int)cut.size() ? '\n' : ' ');
    if (cut.empty())
        cout << '\n';

    return 0;
}
```

### 实现提醒

同城多个警局只算一个源；保留首次访问的归属；输出原边编号。
