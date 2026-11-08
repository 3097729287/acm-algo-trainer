## P1550 Watering Hole G

原题：[P1550](https://www.luogu.com.cn/problem/P1550)

### 从问题到算法

只考虑农场之间的管道会遗漏水源的代价。引入虚拟水源 0 后，打井与铺管道都变成一次连接：打井连接水源与农场，管道连接两个农场。

任何合法供水方案都使每个农场通过某口井连接到 0。反过来，若所有点在含 0 的图中连通，沿路径也必然能找到一个水源。两种方案代价完全一致，所以问题变成包含 n+1 个点的最小生成树。

读取打井费用和费用矩阵，把对称管道只加入一次。Kruskal 按费用从小到大选不成环的边，允许选择多口井，因为那可能比长管道便宜。

### 复杂度

时间 O(n² log n)，空间 O(n²)。

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
    struct E {
        int u, v, w;
    };
    vector<E> e;
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        e.push_back({0, i, x});
    }
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= n; j++) {
            int x;
            cin >> x;
            if (i < j)
                e.push_back({i, j, x});
        }
    sort(e.begin(), e.end(), [](E a, E b) { return a.w < b.w; });
    DSU d(n + 1);
    long long ans = 0;
    for (auto x : e)
        if (d.join(x.u, x.v))
            ans += x.w;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

不能强制只打一口井；虚拟点也要加入并查集。
