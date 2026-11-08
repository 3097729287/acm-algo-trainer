#include <bits/stdc++.h>
using namespace std;

struct Lowlink {
    int n, timer = 0;
    vector<vector<pair<int, int>>> g;
    vector<pair<int, int>> edges;
    vector<int> tin, low, parent, parentEdge, children, size;
    vector<char> bridge, cut;
    vector<vector<int>> blocks;
    Lowlink(int n)
        : n(n), g(n), tin(n), low(n), parent(n, -1), parentEdge(n, -1), children(n), size(n, 1),
          cut(n) {}
    void edge(int a, int b) {
        int id = edges.size();
        edges.push_back({a, b});
        g[a].push_back({b, id});
        g[b].push_back({a, id});
    }
    void build() {
        bridge.assign(edges.size(), 0);
        vector<int> vertices;
        for (int root = 0; root < n; root++)
            if (!tin[root]) {
                vector<pair<int, int>> st = {{root, 0}};
                tin[root] = low[root] = ++timer;
                vertices.push_back(root);
                while (!st.empty()) {
                    int v = st.back().first;
                    int &next = st.back().second;
                    if (next < (int)g[v].size()) {
                        auto [u, id] = g[v][next++];
                        if (id == parentEdge[v])
                            continue;
                        if (!tin[u]) {
                            parent[u] = v;
                            parentEdge[u] = id;
                            children[v]++;
                            tin[u] = low[u] = ++timer;
                            vertices.push_back(u);
                            st.push_back({u, 0});
                        } else
                            low[v] = min(low[v], tin[u]);
                    } else {
                        st.pop_back();
                        int p = parent[v];
                        if (p >= 0) {
                            size[p] += size[v];
                            low[p] = min(low[p], low[v]);
                            bridge[parentEdge[v]] = low[v] > tin[p];
                            if (low[v] >= tin[p]) {
                                if (parent[p] >= 0)
                                    cut[p] = 1;
                                vector<int> block = {p};
                                while (true) {
                                    int u = vertices.back();
                                    vertices.pop_back();
                                    block.push_back(u);
                                    if (u == v)
                                        break;
                                }
                                blocks.push_back(move(block));
                            }
                        } else {
                            cut[v] = children[v] > 1;
                            if (children[v] == 0)
                                blocks.push_back({v});
                            vertices.pop_back();
                        }
                    }
                }
            }
    }
};

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

    int n, m;
    cin >> n >> m;
    Lowlink graph(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        graph.edge(a - 1, b - 1);
    }
    graph.build();
    DSU d(n);
    for (int i = 0; i < m; i++)
        if (!graph.bridge[i])
            d.join(graph.edges[i].first, graph.edges[i].second);
    vector<int> id(n, -1), belong(n);
    int z = 0;
    for (int i = 0; i < n; i++) {
        int r = d.find(i);
        if (id[r] < 0)
            id[r] = z++;
        belong[i] = id[r];
    }
    vector<int> w(z);
    for (int i = 0; i < n; i++)
        if (d.size[d.find(i)] > 1)
            w[belong[i]] = 1;
    vector<vector<int>> g(z);
    for (int i = 0; i < m; i++)
        if (graph.bridge[i]) {
            int a = belong[graph.edges[i].first], b = belong[graph.edges[i].second];
            g[a].push_back(b);
            g[b].push_back(a);
        }
    HLD tree(g);
    vector<int> pref(z), power(n + 1, 1);
    for (int v : tree.order)
        pref[v] = w[v] + (v ? pref[tree.parent[v]] : 0);
    for (int i = 1; i <= n; i++)
        power[i] = 2LL * power[i - 1] % 1000000007;
    int q;
    cin >> q;
    while (q--) {
        int a, b;
        cin >> a >> b;
        int u = belong[a - 1], v = belong[b - 1], l = tree.lca(u, v);
        cout << power[pref[u] + pref[v] - 2 * pref[l] + w[l]] << '\n';
    }

    return 0;
}
