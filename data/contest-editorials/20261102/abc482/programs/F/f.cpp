#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n;
    int m;
    cin >> n >> m;
    vector<pair<int, int>> factors;
    for (long long p = 2; p * p <= n; p += (p == 2 ? 1 : 2)) {
        if (n % p != 0) continue;
        int exponent = 0;
        while (n % p == 0) { n /= p; ++exponent; }
        factors.push_back({int(p % m), exponent});
    }
    if (n > 1) factors.push_back({int(n % m), 1});
    if (factors.empty()) {
        for (int r = 0; r < m; ++r) cout << (r == 1 % m ? 1 : -1) << '\n';
        return 0;
    }
    int layers = factors.size(), inf = 1000000000;
    vector<int> dist(layers * m, inf);
    vector<char> done(layers * m);
    deque<int> q;
    dist[1 % m] = 0; q.push_back(1 % m);
    while (!q.empty()) {
        int id = q.front(); q.pop_front();
        if (done[id]) continue;
        done[id] = 1;
        int layer = id / m, residue = id % m;
        int next_layer = (layer + 1) % layers;
        int cost = layer == 0;
        long long next_residue = residue;
        for (int e = 0; e <= factors[layer].second; ++e) {
            int to = next_layer * m + int(next_residue);
            if (dist[id] + cost < dist[to]) {
                dist[to] = dist[id] + cost;
                // 开始新一轮花费一，其余因子层不增加轮数。
                if (cost == 0) q.push_front(to); else q.push_back(to);
            }
            next_residue = next_residue * factors[layer].first % m;
        }
    }
    // 只读回到第零层的完整轮次；t 必须是正整数。
    for (int r = 0; r < m; ++r) cout << (dist[r] == inf ? -1 : max(1, dist[r])) << '\n';
}
