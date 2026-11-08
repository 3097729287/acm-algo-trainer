#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, K;
    cin >> n >> m >> K;
    vector<vector<pair<int, int>>> g(n);
    while (m--) {
        int u, v, w;
        cin >> u >> v >> w;
        u--;
        v--;
        g[u].push_back({v, w});
        g[v].push_back({u, w});
    }
    const long long INF = 1LL << 60;
    vector<long long> d(n * (K + 1), INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[0] = 0;
    q.push({0, 0});
    while (!q.empty()) {
        auto [dist, state] = q.top();
        q.pop();
        if (dist != d[state])
            continue;
        int used = state / n, v = state % n;
        for (auto [u, w] : g[v])
            for (int take = 0; take <= 1 && used + take <= K; take++) {
                int next = (used + take) * n + u;
                long long nd = dist + (take ? w / 2 : w);
                if (nd < d[next]) {
                    d[next] = nd;
                    q.push({nd, next});
                }
            }
    }
    long long ans = INF;
    for (int k = 0; k <= K; k++)
        ans = min(ans, d[k * n + n - 1]);
    cout << ans << '\n';

    return 0;
}
