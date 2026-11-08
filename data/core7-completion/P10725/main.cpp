#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    for (int &x : a)
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
    const int NEG = -1000000000;
    vector<array<int, 2>> down(n, {NEG, NEG});
    int ans = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        down[v][a[v]] = 0;
        for (int u : g[v])
            if (parent[u] == v) {
                ans = max({ans, down[v][0] + down[u][1] + 1, down[v][1] + down[u][0] + 1});
                for (int c = 0; c < 2; c++)
                    down[v][c] = max(down[v][c], down[u][c] + 1);
            }
    }
    cout << ans << '\n';

    return 0;
}
