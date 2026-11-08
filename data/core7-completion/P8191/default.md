## P8191 Moo Network G

原题：[P8191](https://www.luogu.com.cn/problem/P8191)

### 思路

纵坐标只有 0 到 10。对每个点与每条水平行，只连接横坐标最近的左右邻居，再在这些 O(11n) 条候选边上做 Kruskal。

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
