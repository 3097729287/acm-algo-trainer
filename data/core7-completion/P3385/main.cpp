#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, m;
        cin >> n >> m;
        vector<tuple<int, int, int>> e;
        while (m--) {
            int u, v, w;
            cin >> u >> v >> w;
            u--;
            v--;
            e.push_back({u, v, w});
            if (w >= 0)
                e.push_back({v, u, w});
        }
        const long long INF = 1LL << 60;
        vector<long long> d(n, INF);
        d[0] = 0;
        bool negative = false;
        for (int round = 1; round <= n; round++) {
            bool changed = false;
            for (auto [u, v, w] : e)
                if (d[u] != INF && d[v] > d[u] + w) {
                    d[v] = d[u] + w;
                    changed = true;
                }
            if (!changed)
                break;
            if (round == n)
                negative = true;
        }
        cout << (negative ? "YES" : "NO") << '\n';
    }

    return 0;
}
