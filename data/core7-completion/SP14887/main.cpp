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

    int n, m, start, goal;
    cin >> n >> m >> start >> goal;
    start--;
    goal--;
    vector<long long> w(n);
    for (auto &x : w)
        cin >> x;
    SCC s(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        s.edge(a - 1, b - 1);
    }
    s.build();
    vector<long long> weight(s.count);
    vector<vector<int>> g(s.count);
    vector<int> in(s.count);
    for (int v = 0; v < n; v++) {
        weight[s.component[v]] += w[v];
        for (int u : s.g[v])
            if (s.component[u] != s.component[v]) {
                g[s.component[v]].push_back(s.component[u]);
                in[s.component[u]]++;
            }
    }
    const long long neg = LLONG_MIN / 4;
    vector<long long> dp(s.count, neg);
    dp[s.component[start]] = weight[s.component[start]];
    queue<int> q;
    for (int c = 0; c < s.count; c++)
        if (!in[c])
            q.push(c);
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        for (int u : g[v]) {
            if (dp[v] != neg)
                dp[u] = max(dp[u], dp[v] + weight[u]);
            if (--in[u] == 0)
                q.push(u);
        }
    }
    cout << dp[s.component[goal]] << '\n';

    return 0;
}
