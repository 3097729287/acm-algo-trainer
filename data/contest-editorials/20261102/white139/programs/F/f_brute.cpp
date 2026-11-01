#include <bits/stdc++.h>
using namespace std;
struct Edge { int u, v; long long w; };
int main() {
    int T; cin >> T;
    while (T--) {
        int n; cin >> n;
        vector<Edge> original(n - 1), all;
        vector<vector<pair<int, int>>> g(n);
        vector<vector<bool>> has(n, vector<bool>(n, false));
        long long base = 0;
        for (auto &e : original) {
            cin >> e.u >> e.v >> e.w; --e.u; --e.v;
            has[e.u][e.v] = has[e.v][e.u] = true;
            g[e.u].push_back({e.v, static_cast<int>(e.w)});
            g[e.v].push_back({e.u, static_cast<int>(e.w)});
            base += e.w;
        }
        // 补上全部非树边，每条取保持唯一 MST 的最小整数权值。
        for (int s = 0; s < n; ++s) {
            vector<int> par(n, -1), mx(n, 0), order{s}; par[s] = s;
            for (int i = 0; i < static_cast<int>(order.size()); ++i) {
                int v = order[i];
                for (auto e : g[v]) if (par[e.first] == -1) {
                    par[e.first] = v;
                    mx[e.first] = max(mx[v], e.second);
                    order.push_back(e.first);
                }
            }
            for (int v = s + 1; v < n; ++v) if (!has[s][v]) all.push_back({s, v, mx[v] + 1LL});
        }
        all.insert(all.end(), original.begin(), original.end());
        sort(all.begin(), all.end(), [](Edge a, Edge b) { return a.w < b.w; });
        bool ok = true;
        // 直接在完整候选图上删边、重求 MST，独立于正解的相邻边判据。
        for (Edge ban : original) {
            vector<int> component(n); iota(component.begin(), component.end(), 0);
            int count = 0;
            long long sum = 0;
            for (Edge e : all) {
                if ((e.u == ban.u && e.v == ban.v) || (e.u == ban.v && e.v == ban.u)) continue;
                int a = component[e.u], b = component[e.v];
                if (a == b) continue;
                for (int &c : component) if (c == b) c = a;
                sum += e.w; ++count;
            }
            if (count != n - 1 || sum != base + 1) ok = false;
        }
        cout << (ok ? "Yes\n" : "No\n");
    }
}
