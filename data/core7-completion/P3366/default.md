## P3366 最小生成树

原题：[P3366](https://www.luogu.com.cn/problem/P3366)

### 思路

将边按权值从小到大排序，用并查集判断两端是否已连通。连接两个不同连通块的边才能进入生成树。选满 n−1 条边得到最小生成树；不能选满则图不连通。

### 复杂度

时间 O(m log m)，空间 O(n+m)。

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
    struct E {
        int u, v;
        long long w;
    };
    vector<E> e(m);
    long long total = 0;
    for (auto &x : e) {
        cin >> x.u >> x.v >> x.w;
        total += x.w;
    }
    sort(e.begin(), e.end(), [](E a, E b) { return a.w < b.w; });
    DSU d(n + 1);
    long long answer = 0;
    int used = 0;
    for (auto x : e)
        if (d.join(x.u, x.v)) {
            answer += x.w;
            used++;
        }
    if (used != n - 1)
        cout << "orz\n";
    else
        cout << answer << '\n';
    return 0;
}
```

### 实现提醒

并查集按顶点编号开空间；总权值使用六十四位整数；相同权值任意处理。
