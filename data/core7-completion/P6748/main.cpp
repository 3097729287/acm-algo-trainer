#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<long long> a(n);
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
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    const long long NEG = -(1LL << 60);
    vector<array<long long, 2>> dp(n, {NEG, NEG});
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i], H = ((int)g[v].size() - 1) / 2;
        long long base = 0;
        vector<long long> gains;
        for (int u : g[v])
            if (parent[u] == v) {
                long long low = NEG, high = NEG;
                for (long long w : {a[v], a[u], m}) {
                    long long sub = dp[u][w > a[u]];
                    if (sub == NEG)
                        continue;
                    if (w <= a[v])
                        low = max(low, w + sub);
                    else
                        high = max(high, w + sub);
                }
                base += low;
                if (high > low)
                    gains.push_back(high - low);
            }
        sort(gains.rbegin(), gains.rend());
        vector<long long> prefix(gains.size() + 1);
        for (int j = 0; j < (int)gains.size(); j++)
            prefix[j + 1] = prefix[j] + gains[j];
        for (int state = 0; state < 2; state++)
            if (H >= state)
                dp[v][state] = base + prefix[min((int)gains.size(), H - state)];
    }
    cout << (dp[0][0] == NEG ? -1 : dp[0][0]) << '\n';

    return 0;
}
