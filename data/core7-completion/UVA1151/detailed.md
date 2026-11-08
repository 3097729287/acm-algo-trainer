## UVA1151 买还是建 Buy or Build

原题：[UVA1151](https://www.luogu.com.cn/problem/UVA1151)

### 从问题到算法

购买套餐后，它包含的城市内部可以看作零费用连通，而套餐本身代价固定。枚举购买子集，就把选择套餐与铺普通道路分开。

先在完整平方距离图上用 Prim 得到一棵基础 MST。往图中加入一条零费用边时，可以在原 MST 加这条边形成的环中删去最重边，得到新 MST；反复加入所有套餐内部边后，最优树始终可从“原 MST 加新增零边”中取得。因此不需要为每个子集重新扫描平方条普通边。

对每个套餐子集重新建并查集，累计套餐费，并把同套餐城市合并；再按权值递增扫描基础 MST 的 n−1 条边，连接不同块就付费。所有子集的最小总额即答案。输入按原题先给套餐，再给城市坐标，测试组之间输出空行。

### 复杂度

时间 O(n²+2^q·(n+套餐总人数))，空间 O(n+套餐总人数)。

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

    int tests;
    cin >> tests;
    for (int test = 0; test < tests; test++) {
        int n, q;
        cin >> n >> q;
        vector<vector<int>> packages(q);
        vector<long long> price(q);
        for (int i = 0; i < q; i++) {
            int size;
            cin >> size >> price[i];
            packages[i].resize(size);
            for (int &v : packages[i]) {
                cin >> v;
                v--;
            }
        }
        vector<long long> x(n), y(n);
        for (int i = 0; i < n; i++)
            cin >> x[i] >> y[i];
        vector<long long> distance(n, LLONG_MAX);
        vector<int> from(n, -1);
        vector<char> used(n);
        vector<tuple<long long, int, int>> edges;
        distance[0] = 0;
        for (int step = 0; step < n; step++) {
            int v = -1;
            for (int i = 0; i < n; i++)
                if (!used[i] && (v < 0 || distance[i] < distance[v]))
                    v = i;
            used[v] = 1;
            if (from[v] >= 0)
                edges.push_back({distance[v], from[v], v});
            for (int u = 0; u < n; u++)
                if (!used[u]) {
                    long long dx = x[u] - x[v], dy = y[u] - y[v], cost = dx * dx + dy * dy;
                    if (cost < distance[u]) {
                        distance[u] = cost;
                        from[u] = v;
                    }
                }
        }
        sort(edges.begin(), edges.end());
        long long answer = LLONG_MAX;
        for (int mask = 0; mask < (1 << q); mask++) {
            DSU d(n);
            long long cost = 0;
            for (int i = 0; i < q; i++)
                if ((mask >> i) & 1) {
                    cost += price[i];
                    for (int v : packages[i])
                        d.join(packages[i][0], v);
                }
            for (auto [w, a, b] : edges)
                if (d.join(a, b))
                    cost += w;
            answer = min(answer, cost);
        }
        if (test)
            cout << '\n';
        cout << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

套餐费一次支付；普通路费为平方距离；每个子集重建并查集。
