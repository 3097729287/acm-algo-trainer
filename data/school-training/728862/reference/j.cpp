#include <bits/stdc++.h>
using namespace std;
using ll = long long;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<ll> x(n), y(n), c(n), k(n);
    for (int i = 0; i < n; ++i) cin >> x[i] >> y[i];
    for (ll &v : c) cin >> v;
    for (ll &v : k) cin >> v;
    // 虚拟点零已加入：到城市 i 的初始最优边就是建站费用。
    vector<ll> best = c;
    vector<int> from(n, -1), stations;
    vector<pair<int, int>> wires;
    vector<bool> used(n, false);
    ll total = 0;
    for (int step = 0; step < n; ++step) {
        int u = -1;
        for (int i = 0; i < n; ++i) {
            if (!used[i] && (u == -1 || best[i] < best[u])) u = i;
        }
        used[u] = true;
        total += best[u];
        if (from[u] == -1) stations.push_back(u + 1);
        else wires.push_back({from[u] + 1, u + 1});
        for (int v = 0; v < n; ++v) {
            if (used[v]) continue;
            ll cost = (abs(x[u] - x[v]) + abs(y[u] - y[v])) * (k[u] + k[v]);
            if (cost < best[v]) {
                best[v] = cost;
                from[v] = u;
            }
        }
    }
    cout << total << '\n' << stations.size() << '\n';
    for (int v : stations) cout << v << ' ';
    cout << '\n' << wires.size() << '\n';
    for (auto edge : wires) cout << edge.first << ' ' << edge.second << '\n';
}
