#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int K, n, m;
    cin >> K >> n >> m;
    vector<vector<array<int, 3>>> g(n);
    while (m--) {
        int u, v, t, h;
        cin >> u >> v >> t >> h;
        u--;
        v--;
        g[u].push_back({v, t, h});
        g[v].push_back({u, t, h});
    }
    int s, t;
    cin >> s >> t;
    s--;
    t--;
    const long long INF = 1LL << 60;
    vector<long long> d(n * K, INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[s] = 0;
    q.push({0, s});
    while (!q.empty()) {
        auto [dist, state] = q.top();
        q.pop();
        if (d[state] != dist)
            continue;
        int h = state / n, v = state % n;
        for (auto [u, cost, damage] : g[v])
            if (h + damage < K) {
                int next = (h + damage) * n + u;
                if (d[next] > dist + cost) {
                    d[next] = dist + cost;
                    q.push({d[next], next});
                }
            }
    }
    long long ans = INF;
    for (int h = 0; h < K; h++)
        ans = min(ans, d[h * n + t]);
    cout << (ans == INF ? -1 : ans) << '\n';

    return 0;
}
