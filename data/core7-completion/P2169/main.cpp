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
    vector<tuple<int, int, int>> edges;
    while (m--) {
        int a, b, w;
        cin >> a >> b >> w;
        a--;
        b--;
        s.edge(a, b);
        edges.push_back({a, b, w});
    }
    s.build();
    vector<vector<pair<int, int>>> g(s.count);
    for (auto [a, b, w] : edges)
        if (s.component[a] != s.component[b])
            g[s.component[a]].push_back({s.component[b], w});
    const long long inf = LLONG_MAX / 4;
    vector<long long> d(s.count, inf);
    int start = s.component[0], goal = s.component[n - 1];
    d[start] = 0;
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    q.push({0, start});
    while (!q.empty()) {
        auto [dist, v] = q.top();
        q.pop();
        if (dist != d[v])
            continue;
        for (auto [u, w] : g[v])
            if (d[u] > dist + w) {
                d[u] = dist + w;
                q.push({d[u], u});
            }
    }
    cout << d[goal] << '\n';

    return 0;
}
