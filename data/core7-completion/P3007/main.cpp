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
    SCC s(2 * n);
    while (m--) {
        int a, b;
        char x, y;
        cin >> a >> x >> b >> y;
        int u = 2 * (a - 1) + (x == 'Y'), v = 2 * (b - 1) + (y == 'Y');
        s.edge(u ^ 1, v);
        s.edge(v ^ 1, u);
    }
    s.build();
    for (int i = 0; i < n; i++)
        if (s.component[2 * i] == s.component[2 * i + 1]) {
            cout << "IMPOSSIBLE\n";
            return 0;
        }
    auto reach = [&](int a, int b) {
        vector<char> seen(2 * n);
        vector<int> st = {a};
        seen[a] = 1;
        while (!st.empty()) {
            int v = st.back();
            st.pop_back();
            if (v == b)
                return true;
            for (int u : s.g[v])
                if (!seen[u]) {
                    seen[u] = 1;
                    st.push_back(u);
                }
        }
        return false;
    };
    for (int i = 0; i < n; i++)
        cout << (reach(2 * i, 2 * i + 1) ? 'Y' : reach(2 * i + 1, 2 * i) ? 'N' : '?');
    cout << '\n';

    return 0;
}
