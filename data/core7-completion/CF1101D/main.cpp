#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int V = 1;
    for (int &x : a) {
        cin >> x;
        V = max(V, x);
    }
    vector<int> spf(V + 1);
    for (int p = 2; p <= V; p++)
        if (!spf[p])
            for (int j = p; j <= V; j += p)
                if (!spf[j])
                    spf[j] = p;
    vector<vector<int>> f(n), dp(n);
    for (int i = 0; i < n; i++) {
        int x = a[i];
        while (x > 1) {
            int p = spf[x];
            f[i].push_back(p);
            while (x % p == 0)
                x /= p;
        }
        dp[i].assign(f[i].size(), 1);
    }
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    int ans = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        for (int x : dp[v])
            ans = max(ans, x);
        for (int u : g[v])
            if (parent[u] == v)
                for (int j = 0; j < (int)f[v].size(); j++)
                    for (int k = 0; k < (int)f[u].size(); k++)
                        if (f[v][j] == f[u][k]) {
                            ans = max(ans, dp[v][j] + dp[u][k]);
                            dp[v][j] = max(dp[v][j], dp[u][k] + 1);
                        }
    }
    cout << ans << '\n';

    return 0;
}
