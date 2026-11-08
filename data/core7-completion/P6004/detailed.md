## P6004 Wormhole Sort S

原题：[P6004](https://www.luogu.com.cn/problem/P6004)

### 从问题到算法

同一连通块内，沿道路的相邻交换可以生成任意排列，因此牛能被送回目标位置，当且仅当它当前的位置和目标位置属于同一连通块。不同块之间无法交换，这个条件也是必要的。

若要求最窄虫洞至少为 W，就只能使用宽度不小于 W 的边。用并查集连接这些边，再检查每个位置 i 与 permutation[i] 是否同块。W 越小可用边越多，条件单调。

二分最大可行宽度。若输入本来已经有序，不需要经过任何虫洞，原题要求输出 −1，必须在二分前特判。

### 复杂度

时间 O((n+m) log W·α(n))，空间 O(n+m)。

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

    int n, m;
    cin >> n >> m;
    vector<int> p(n + 1);
    bool sorted = true;
    for (int i = 1; i <= n; i++) {
        cin >> p[i];
        sorted &= p[i] == i;
    }
    vector<tuple<int, int, int>> edges(m);
    int maximum = 0;
    for (auto &[a, b, w] : edges) {
        cin >> a >> b >> w;
        maximum = max(maximum, w);
    }
    if (sorted) {
        cout << -1 << '\n';
        return 0;
    }
    auto ok = [&](int limit) {
        DSU d(n + 1);
        for (auto [a, b, w] : edges)
            if (w >= limit)
                d.join(a, b);
        for (int i = 1; i <= n; i++)
            if (d.find(i) != d.find(p[i]))
                return false;
        return true;
    };
    int l = 0, r = maximum;
    while (l < r) {
        int mid = l + (r - l + 1) / 2;
        if (ok(mid))
            l = mid;
        else
            r = mid - 1;
    }
    cout << l << '\n';

    return 0;
}
```

### 实现提醒

保留宽度大于等于阈值的边；检查牛与目标位置；已排序输出 -1。
