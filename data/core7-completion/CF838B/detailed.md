## CF838B Diverging Directions

原题：[CF838B](https://www.luogu.com.cn/problem/CF838B)

### 从问题到算法

所有普通树边都从根向下，所以不经过根时，只能到达当前点的后代。若 v 是 u 后代，直接路径长为 dist[v]−dist[u]，任何绕根路线都更长。

否则必须在 u 的某个后代 x 处走回根边，再从根到 v，费用为 dist[x]−dist[u]+back[x]+dist[v]。因此只需查询 u 子树内 dist[x]+back[x] 的最小值。Euler 序把子树变成连续区间。

修改一条树边增加 delta，会让其孩子整个子树的 dist 同增 delta，于是线段树对应区间加 delta；修改回根边只使一个点的 back 改变，做单点加。当前 dist[u] 可由该点维护值减去 back[u] 得到。

Euler 遍历用显式栈，避免深链递归；区间加与区间最小值用懒标记线段树，所有路长使用 long long。

### 复杂度

时间 O((n+q) log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct MinTree {
    int n;
    vector<long long> value, tag;
    MinTree(const vector<long long> &a) : n(a.size()), value(4 * n), tag(4 * n) {
        build(1, 0, n - 1, a);
    }
    void build(int p, int l, int r, const vector<long long> &a) {
        if (l == r) {
            value[p] = a[l];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m, a);
        build(p * 2 + 1, m + 1, r, a);
        value[p] = min(value[p * 2], value[p * 2 + 1]);
    }
    void apply(int p, long long x) {
        value[p] += x;
        tag[p] += x;
    }
    void push(int p) {
        if (tag[p]) {
            apply(p * 2, tag[p]);
            apply(p * 2 + 1, tag[p]);
            tag[p] = 0;
        }
    }
    void add(int p, int l, int r, int a, int b, long long x) {
        if (a <= l && r <= b) {
            apply(p, x);
            return;
        }
        push(p);
        int m = (l + r) / 2;
        if (a <= m)
            add(p * 2, l, m, a, b, x);
        if (b > m)
            add(p * 2 + 1, m + 1, r, a, b, x);
        value[p] = min(value[p * 2], value[p * 2 + 1]);
    }
    long long query(int p, int l, int r, int a, int b) {
        if (a <= l && r <= b)
            return value[p];
        push(p);
        int m = (l + r) / 2;
        long long ans = LLONG_MAX / 4;
        if (a <= m)
            ans = min(ans, query(p * 2, l, m, a, b));
        if (b > m)
            ans = min(ans, query(p * 2 + 1, m + 1, r, a, b));
        return ans;
    }
    void add(int l, int r, long long x) { add(1, 0, n - 1, l, r, x); }
    long long query(int l, int r) { return query(1, 0, n - 1, l, r); }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    int m = 2 * n - 2;
    vector<int> from(m), to(m);
    vector<long long> w(m), back(n), distance(n);
    vector<vector<pair<int, int>>> g(n);
    for (int i = 0; i < m; i++) {
        cin >> from[i] >> to[i] >> w[i];
        from[i]--;
        to[i]--;
        if (i < n - 1)
            g[from[i]].push_back({to[i], i});
        else
            back[from[i]] = w[i];
    }
    vector<int> tin(n), tout(n);
    int timer = 0;
    vector<pair<int, int>> stack = {{0, 0}};
    tin[0] = timer++;
    while (!stack.empty()) {
        int v = stack.back().first;
        int &next = stack.back().second;
        if (next < (int)g[v].size()) {
            auto [u, id] = g[v][next++];
            distance[u] = distance[v] + w[id];
            tin[u] = timer++;
            stack.push_back({u, 0});
        } else {
            tout[v] = timer - 1;
            stack.pop_back();
        }
    }
    vector<long long> initial(n);
    for (int v = 0; v < n; v++)
        initial[tin[v]] = distance[v] + back[v];
    MinTree tree(initial);
    while (q--) {
        int op, a;
        long long b;
        cin >> op >> a >> b;
        a--;
        if (op == 1) {
            long long delta = b - w[a];
            w[a] = b;
            if (a < n - 1)
                tree.add(tin[to[a]], tout[to[a]], delta);
            else {
                int v = from[a];
                back[v] += delta;
                tree.add(tin[v], tin[v], delta);
            }
        } else {
            int v = b - 1;
            long long da = tree.query(tin[a], tin[a]) - back[a],
                      db = tree.query(tin[v], tin[v]) - back[v];
            if (tin[a] <= tin[v] && tin[v] <= tout[a])
                cout << db - da << '\n';
            else
                cout << tree.query(tin[a], tout[a]) - da + db << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

前 n−1 条是向下树边；回根边按实际起点映射；修改后查询使用当前距离。
