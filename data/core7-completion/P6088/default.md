## P6088 字符串树

原题：[P6088](https://www.luogu.com.cn/problem/P6088)

### 思路

所有以 S 为前缀的标签在字典序中连续。将标签排序离散化，每个树点保存根路径标签频次的持久化线段树，查询以 u、v 两根减去两份 LCA 根得到路径频次。

### 复杂度

预处理 O(n log n)，每问 O(log n+|S| log n)，空间 O(n log n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct HLD {
    int n;
    vector<int> parent, depth, size, heavy, head, pos, at, order;
    HLD(const vector<vector<int>> &g, int root = 0)
        : n(g.size()), parent(n, -1), depth(n), size(n, 1), heavy(n, -1), head(n), pos(n), at(n) {
        parent[root] = root;
        order = {root};
        for (int i = 0; i < (int)order.size(); i++) {
            int v = order[i];
            for (int u : g[v])
                if (parent[u] < 0) {
                    parent[u] = v;
                    depth[u] = depth[v] + 1;
                    order.push_back(u);
                }
        }
        for (int i = n - 1; i > 0; i--) {
            int v = order[i], p = parent[v];
            size[p] += size[v];
            if (heavy[p] < 0 || size[v] > size[heavy[p]])
                heavy[p] = v;
        }
        vector<pair<int, int>> st = {{root, root}};
        int timer = 0;
        while (!st.empty()) {
            auto [v, h] = st.back();
            st.pop_back();
            for (; v >= 0; v = heavy[v]) {
                head[v] = h;
                pos[v] = timer;
                at[timer++] = v;
                for (int u : g[v])
                    if (parent[u] == v && u != heavy[v])
                        st.push_back({u, u});
            }
        }
    }
    int lca(int a, int b) const {
        while (head[a] != head[b]) {
            if (depth[head[a]] < depth[head[b]])
                swap(a, b);
            a = parent[head[a]];
        }
        return depth[a] < depth[b] ? a : b;
    }
    int jump(int v, int d) const {
        while (d > depth[v] - depth[head[v]]) {
            d -= depth[v] - depth[head[v]] + 1;
            v = parent[head[v]];
        }
        return at[pos[v] - d];
    }
    int distance(int a, int b) const { return depth[a] + depth[b] - 2 * depth[lca(a, b)]; }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> g(n);
    vector<tuple<int, int, string>> edges;
    vector<string> words;
    for (int i = 1; i < n; i++) {
        int a, b;
        string s;
        cin >> a >> b >> s;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
        edges.push_back({a, b, s});
        words.push_back(s);
    }
    sort(words.begin(), words.end());
    words.erase(unique(words.begin(), words.end()), words.end());
    HLD tree(g);
    vector<int> label(n), root(n);
    for (auto [a, b, s] : edges) {
        if (tree.parent[a] == b)
            swap(a, b);
        label[b] = lower_bound(words.begin(), words.end(), s) - words.begin();
    }
    struct Node {
        int l = 0, r = 0, count = 0;
    };
    vector<Node> pool(1);
    pool.reserve(20LL * n + 1);
    function<int(int, int, int, int)> insert = [&](int old, int l, int r, int x) {
        int cur = pool.size();
        pool.push_back(pool[old]);
        pool[cur].count++;
        if (l < r) {
            int mid = (l + r) / 2;
            if (x <= mid)
                pool[cur].l = insert(pool[old].l, l, mid, x);
            else
                pool[cur].r = insert(pool[old].r, mid + 1, r, x);
        }
        return cur;
    };
    int M = words.size();
    for (int u : tree.order)
        if (u)
            root[u] = insert(root[tree.parent[u]], 0, M - 1, label[u]);
    function<int(int, int, int, int, int, int, int)> query = [&](int a, int b, int c, int l, int r,
                                                                 int L, int R) {
        if (L <= l && r <= R)
            return pool[a].count + pool[b].count - 2 * pool[c].count;
        int mid = (l + r) / 2, ans = 0;
        if (L <= mid)
            ans += query(pool[a].l, pool[b].l, pool[c].l, l, mid, L, R);
        if (R > mid)
            ans += query(pool[a].r, pool[b].r, pool[c].r, mid + 1, r, L, R);
        return ans;
    };
    int q;
    cin >> q;
    while (q--) {
        int a, b;
        string s;
        cin >> a >> b >> s;
        a--;
        b--;
        int L = lower_bound(words.begin(), words.end(), s) - words.begin(),
            R = lower_bound(words.begin(), words.end(), s + '{') - words.begin() - 1;
        if (L > R)
            cout << 0 << '\n';
        else
            cout << query(root[a], root[b], root[tree.lca(a, b)], 0, M - 1, L, R) << '\n';
    }

    return 0;
}
```

### 实现提醒

标签是边权；前缀上界用 S 加左花括号；LCA 版本减两次。
