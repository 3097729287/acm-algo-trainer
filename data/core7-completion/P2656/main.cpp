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
    struct E {
        int u, v, w, k;
    };
    vector<E> edges;
    for (int i = 0; i < m; i++) {
        int u, v, w;
        string k;
        cin >> u >> v >> w >> k;
        u--;
        v--;
        int rate = 0;
        auto dot = k.find('.');
        if (dot != string::npos && dot + 1 < k.size())
            rate = k[dot + 1] - '0';
        edges.push_back({u, v, w, rate});
        s.edge(u, v);
    }
    int start;
    cin >> start;
    start--;
    s.build();
    vector<long long> value(s.count), dp(s.count, LLONG_MIN / 4);
    vector<vector<pair<int, int>>> g(s.count);
    vector<int> in(s.count);
    for (auto e : edges) {
        int u = s.component[e.u], v = s.component[e.v];
        if (u == v) {
            long long w = e.w;
            while (w) {
                value[u] += w;
                w = w * e.k / 10;
            }
        } else {
            g[u].push_back({v, e.w});
            in[v]++;
        }
    }
    queue<int> q;
    for (int i = 0; i < s.count; i++)
        if (!in[i])
            q.push(i);
    dp[s.component[start]] = value[s.component[start]];
    long long ans = dp[s.component[start]];
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        ans = max(ans, dp[v]);
        for (auto [u, w] : g[v]) {
            if (dp[v] >= 0)
                dp[u] = max(dp[u], dp[v] + w + value[u]);
            if (!--in[u])
                q.push(u);
        }
    }
    cout << ans << '\n';

    return 0;
}
