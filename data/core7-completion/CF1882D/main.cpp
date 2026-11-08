#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<long long> a(n), ans(n);
        for (auto &x : a)
            cin >> x;
        vector<vector<int>> g(n);
        for (int i = 1; i < n; i++) {
            int u, v;
            cin >> u >> v;
            u--;
            v--;
            g[u].push_back(v);
            g[v].push_back(u);
        }
        vector<int> parent(n, -1), size(n, 1), order = {0};
        parent[0] = 0;
        for (int i = 0; i < n; i++)
            for (int u : g[order[i]])
                if (u != parent[order[i]]) {
                    parent[u] = order[i];
                    order.push_back(u);
                }
        for (int i = n - 1; i > 0; i--) {
            int v = order[i], p = parent[v];
            size[p] += size[v];
            ans[0] += (a[v] ^ a[p]) * size[v];
        }
        for (int i = 1; i < n; i++) {
            int v = order[i], p = parent[v];
            ans[v] = ans[p] + (a[v] ^ a[p]) * (n - 2LL * size[v]);
        }
        for (long long x : ans)
            cout << x << ' ';
        cout << '\n';
    }

    return 0;
}
