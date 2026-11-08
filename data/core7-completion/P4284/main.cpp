#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<pair<int, long double>>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        long double p;
        cin >> a >> b >> p;
        a--;
        b--;
        p /= 100;
        g[a].push_back({b, p});
        g[b].push_back({a, p});
    }
    vector<long double> self(n), down(n), outside(n, 1), edge(n);
    for (auto &x : self) {
        cin >> x;
        x /= 100;
    }
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (auto [u, p] : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                edge[u] = p;
                order.push_back(u);
            }
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        down[v] = 1 - self[v];
        for (auto [u, p] : g[v])
            if (parent[u] == v)
                down[v] *= 1 - p + p * down[u];
    }
    long double ans = 0;
    for (int v : order) {
        ans += 1 - down[v] * outside[v];
        vector<int> children;
        vector<long double> factors;
        for (auto [u, p] : g[v])
            if (parent[u] == v) {
                children.push_back(u);
                factors.push_back(1 - p + p * down[u]);
            }
        int z = children.size();
        vector<long double> prefix(z + 1, 1), suffix(z + 1, 1);
        for (int i = 0; i < z; i++)
            prefix[i + 1] = prefix[i] * factors[i];
        for (int i = z - 1; i >= 0; i--)
            suffix[i] = suffix[i + 1] * factors[i];
        for (int i = 0; i < z; i++) {
            int u = children[i];
            long double no = outside[v] * (1 - self[v]) * prefix[i] * suffix[i + 1];
            outside[u] = 1 - edge[u] + edge[u] * no;
        }
    }
    cout << fixed << setprecision(6) << ans << '\n';

    return 0;
}
