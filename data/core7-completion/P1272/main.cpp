#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, P;
    cin >> n >> P;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        g[u - 1].push_back(v - 1);
    }
    const int INF = 1000000;
    vector<vector<int>> dp(n, vector<int>(P + 1, INF));
    vector<int> size(n);
    function<void(int)> dfs = [&](int v) {
        size[v] = 1;
        dp[v][1] = g[v].size();
        for (int u : g[v]) {
            dfs(u);
            vector<int> next = dp[v];
            for (int s = 1; s <= min(P, size[v]); s++)
                for (int j = 1; j <= min(size[u], P - s); j++)
                    next[s + j] = min(next[s + j], dp[v][s] + dp[u][j] - 1);
            dp[v].swap(next);
            size[v] += size[u];
        }
    };
    dfs(0);
    int ans = INF;
    for (int v = 0; v < n; v++)
        ans = min(ans, dp[v][P] + (v != 0));
    cout << ans << '\n';

    return 0;
}
