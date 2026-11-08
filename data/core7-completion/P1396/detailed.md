## P1396 营救

原题：[P1396](https://www.luogu.com.cn/problem/P1396)

### 从问题到算法

已经选出的边形成若干互不相交的连通块。下一条连接不同连通块的最小边，对跨越相应割的任何生成树都是安全选择：若某棵最优树没有它，加入后产生的环中可以删除一条不更小的跨块边，总代价不会增加。

依次处理排好序的边，若两端代表元相同，加入会成环，应跳过；否则合并并累计边权。并查集采用路径压缩与按大小合并。

把所有权值不超过 W 的边加入后，两点连通等价于存在最大边权不超过 W 的路径。排序扫描中首次连通的阈值正是所求。

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
    int s, t;
    cin >> s >> t;
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
    if (s == t) {
        cout << 0 << '\n';
        return 0;
    }
    for (auto x : e) {
        d.join(x.u, x.v);
        if (d.find(s) == d.find(t)) {
            cout << x.w << '\n';
            return 0;
        }
    }
    return 0;
}
```

### 实现提醒

并查集按顶点编号开空间；总权值使用六十四位整数；相同权值任意处理。
