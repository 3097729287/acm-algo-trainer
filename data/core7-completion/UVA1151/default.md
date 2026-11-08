## UVA1151 买还是建 Buy or Build

原题：[UVA1151](https://www.luogu.com.cn/problem/UVA1151)

### 思路

套餐至多八个，枚举购买子集，把每个套餐城市先合并，再用最小生成树边补齐网络。基础道路的 MST 可先用 Prim 求出；加入零费用套餐边后，只在这棵 MST 上继续 Kruskal 就足够。

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
