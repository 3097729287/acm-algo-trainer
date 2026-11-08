#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, a, b, c;
    cin >> n >> m >> a >> b >> c;
    int N = n * m;
    vector<long long> w(N);
    for (auto &x : w)
        cin >> x;
    auto dijkstra = [&](int s) {
        const long long INF = 1LL << 62;
        vector<long long> d(N, INF);
        priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                       greater<pair<long long, int>>>
            q;
        d[s] = w[s];
        q.push({d[s], s});
        while (!q.empty()) {
            auto [dist, v] = q.top();
            q.pop();
            if (d[v] != dist)
                continue;
            int x = v / m, y = v % m;
            for (int u :
                 {x ? v - m : -1, x + 1 < n ? v + m : -1, y ? v - 1 : -1, y + 1 < m ? v + 1 : -1})
                if (u >= 0 && d[u] > dist + w[u]) {
                    d[u] = dist + w[u];
                    q.push({d[u], u});
                }
        }
        return d;
    };
    auto x = dijkstra(a - 1), y = dijkstra((n - 1) * m + b - 1), z = dijkstra((n - 1) * m + c - 1);
    long long ans = LLONG_MAX;
    for (int v = 0; v < N; v++)
        ans = min(ans, x[v] + y[v] + z[v] - 2 * w[v]);
    cout << ans << '\n';

    return 0;
}
