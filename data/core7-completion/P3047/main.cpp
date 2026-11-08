#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    int width = k + 1;
    vector<int> down(n * width), all(n * width), parent(n, -1), order = {0};
    for (int i = 0; i < n; i++)
        cin >> down[i * width];
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (u != parent[order[i]]) {
                parent[u] = order[i];
                order.push_back(u);
            }
    for (int i = n - 1; i > 0; i--) {
        int v = order[i], p = parent[v];
        for (int d = 1; d <= k; d++)
            down[p * width + d] += down[v * width + d - 1];
    }
    all = down;
    for (int i = 1; i < n; i++) {
        int v = order[i], p = parent[v];
        for (int d = 1; d <= k; d++)
            all[v * width + d] += all[p * width + d - 1] - (d >= 2 ? down[v * width + d - 2] : 0);
    }
    for (int v = 0; v < n; v++) {
        long long ans = 0;
        for (int d = 0; d <= k; d++)
            ans += all[v * width + d];
        cout << ans << '\n';
    }

    return 0;
}
