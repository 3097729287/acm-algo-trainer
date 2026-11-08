## P8097 Farm Updates G

原题：[P8097](https://www.luogu.com.cn/problem/P8097)

### 从问题到算法

从后向前看，每个农场第一次恢复为“有关”时，正好找到了它在正向过程中的最后有关时刻。逆序 R 会恢复一条边，逆序 D 会激活一个农场，这两类操作只会增加相关性，适合并查集。

逆序 A 本来应该删边，但题目保证加边时两端都活跃，所以这条边在更早时刻即使保留，也只会连接两个本来就有关的点，不会凭空把无关块变为有关。随着逆序进行，它们仍保持活跃。因此可以忽略这个删边，整个逆过程只剩合并与激活。

每个并查集块保存是否含活跃点，以及其中尚未确定答案的顶点列表。激活或合并后，只要块变得有关，就为列表内所有点写下当前时间并清空。每个点只被写一次；列表按小块并入大块，避免反复搬运过多。

先在最终保留的道路上合并，用最终仍活跃的农场给出时间 Q 的答案，再从第 Q 次操作倒退。撤销第 i 次操作后是时刻 i−1，不能误写成 i。

### 复杂度

时间 O((n+q) log n)，空间 O(n+q)。

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

struct Operation {
    char kind;
    int x, y = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<Operation> operations(q);
    vector<pair<int, int>> edges;
    vector<char> removed, active(n, 1);
    for (auto &op : operations) {
        cin >> op.kind >> op.x;
        op.x--;
        if (op.kind == 'A') {
            cin >> op.y;
            op.y--;
            edges.push_back({op.x, op.y});
            removed.push_back(0);
        } else if (op.kind == 'R')
            removed[op.x] = 1;
        else
            active[op.x] = 0;
    }
    DSU d(n);
    vector<char> relevant(n);
    vector<vector<int>> pending(n);
    vector<int> answer(n, -1);
    for (int i = 0; i < n; i++)
        pending[i] = {i};
    auto mark = [&](int root, int time) {
        root = d.find(root);
        relevant[root] = 1;
        for (int v : pending[root])
            answer[v] = time;
        pending[root].clear();
    };
    auto unite = [&](int a, int b, int time) {
        a = d.find(a);
        b = d.find(b);
        if (a == b)
            return;
        if (d.size[a] < d.size[b])
            swap(a, b);
        d.p[b] = a;
        d.size[a] += d.size[b];
        pending[a].insert(pending[a].end(), pending[b].begin(), pending[b].end());
        pending[b].clear();
        relevant[a] |= relevant[b];
        if (relevant[a])
            mark(a, time);
    };
    for (int i = 0; i < (int)edges.size(); i++)
        if (!removed[i])
            unite(edges[i].first, edges[i].second, q);
    for (int v = 0; v < n; v++)
        if (active[v])
            mark(v, q);
    for (int i = q - 1; i >= 0; i--) {
        auto op = operations[i];
        if (op.kind == 'D')
            mark(op.x, i);
        else if (op.kind == 'R')
            unite(edges[op.x].first, edges[op.x].second, i);
    }
    for (int x : answer)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

逆序时间为 i−1；最后仍有关的点答案 Q；忽略 A 依赖加边两端活跃的原题保证。
