## P8191 Moo Network G

原题：[P8191](https://www.luogu.com.cn/problem/P8191)

### 从问题到算法

完整欧氏图有平方条边，但每个点只落在十一种纵坐标之一。把每行按横坐标排序，对点 u 在任一行中找到横坐标刚不小于它的点和前一个点，加入这两条候选边。

为什么可以省掉其它边 u−v？在 v 所在行中，先连接从 u 朝 v 方向的最近点，再沿这一行的相邻点走到 v。第一条边纵坐标差与 u−v 相同、横差更小，后续横向相邻边的长度也都不超过 u−v。因此每条被省掉的完整图边，其两端在候选图中已经由不更重的边相连。

这说明每个权值阈值下两图连通性相同，Kruskal 选出的最小生成树总权也相同。候选边权保存距离平方，排序后做并查集合并，避免开方。坐标相同或边重复都不影响正确性。

### 复杂度

时间 O(11n log n)，空间 O(11n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> x(n);
    vector<int> y(n);
    array<vector<int>, 11> rows;
    for (int i = 0; i < n; i++) {
        cin >> x[i] >> y[i];
        rows[y[i]].push_back(i);
    }
    for (auto &row : rows)
        sort(row.begin(), row.end(), [&](int a, int b) { return x[a] < x[b]; });
    vector<tuple<long long, int, int>> edges;
    auto connect = [&](int a, int b) {
        if (a == b)
            return;
        long long dx = x[a] - x[b], dy = y[a] - y[b];
        edges.push_back({dx * dx + dy * dy, a, b});
    };
    for (int i = 0; i < n; i++)
        for (auto &row : rows) {
            auto it = lower_bound(row.begin(), row.end(), x[i],
                                  [&](int a, long long value) { return x[a] < value; });
            if (it != row.end()) {
                if (*it != i)
                    connect(i, *it);
                else if (next(it) != row.end())
                    connect(i, *next(it));
            }
            if (it != row.begin())
                connect(i, *prev(it));
        }
    sort(edges.begin(), edges.end());
    DSU d(n);
    long long answer = 0;
    for (auto [w, a, b] : edges)
        if (d.join(a, b))
            answer += w;
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

边权是平方距离；每行找左右近邻；坐标乘法用 long long。
