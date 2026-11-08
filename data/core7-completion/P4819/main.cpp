#include <bits/stdc++.h>
using namespace std;

struct SCC {
    int n, count = 0;
    vector<vector<int>> g, rev;
    vector<int> component;
    explicit SCC(int n) : n(n), g(n), rev(n), component(n, -1) {}
    void edge(int a, int b) {
        g[a].push_back(b);
        rev[b].push_back(a);
    }
    void build() {
        vector<char> seen(n);
        vector<int> order;
        for (int start = 0; start < n; start++)
            if (!seen[start]) {
                vector<pair<int, int>> st = {{start, 0}};
                seen[start] = true;
                while (!st.empty()) {
                    int v = st.back().first;
                    int &i = st.back().second;
                    if (i < (int)g[v].size()) {
                        int u = g[v][i++];
                        if (!seen[u]) {
                            seen[u] = true;
                            st.push_back({u, 0});
                        }
                    } else {
                        order.push_back(v);
                        st.pop_back();
                    }
                }
            }
        reverse(order.begin(), order.end());
        for (int start : order)
            if (component[start] < 0) {
                vector<int> st = {start};
                component[start] = count;
                while (!st.empty()) {
                    int v = st.back();
                    st.pop_back();
                    for (int u : rev[v])
                        if (component[u] < 0) {
                            component[u] = count;
                            st.push_back(u);
                        }
                }
                count++;
            }
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    SCC s(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        s.edge(a - 1, b - 1);
    }
    s.build();
    vector<int> size(s.count), in(s.count);
    vector<pair<int, int>> edges;
    for (int v = 0; v < n; v++) {
        size[s.component[v]]++;
        for (int u : s.g[v])
            if (s.component[v] != s.component[u])
                edges.push_back({s.component[v], s.component[u]});
    }
    sort(edges.begin(), edges.end());
    edges.erase(unique(edges.begin(), edges.end()), edges.end());
    vector<vector<int>> g(s.count);
    for (auto [a, b] : edges) {
        g[a].push_back(b);
        in[b]++;
    }
    int risk = count(in.begin(), in.end(), 0);
    for (int c = 0; c < s.count; c++)
        if (!in[c] && size[c] == 1) {
            bool ok = true;
            for (int u : g[c])
                if (in[u] == 1)
                    ok = false;
            if (ok) {
                risk--;
                break;
            }
        }
    cout << fixed << setprecision(6) << 1.0 - (double)risk / n << '\n';

    return 0;
}
