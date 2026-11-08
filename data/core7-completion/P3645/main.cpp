#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    int B = max(2, (int)sqrt(n) + 1), start = 0, goal = 0;
    vector<vector<int>> dogs(n);
    for (int i = 0; i < m; i++) {
        int b, p;
        cin >> b >> p;
        dogs[b].push_back(p);
        if (i == 0)
            start = b;
        if (i == 1)
            goal = b;
    }
    for (auto &v : dogs) {
        sort(v.begin(), v.end());
        v.erase(unique(v.begin(), v.end()), v.end());
    }
    const int INF = 1000000000;
    vector<int> d(n * B, INF);
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> heap;
    d[start] = 0;
    heap.push({0, start});
    auto relax = [&](int state, int value) {
        if (value < d[state]) {
            d[state] = value;
            heap.push({value, state});
        }
    };
    while (!heap.empty()) {
        auto [dist, state] = heap.top();
        heap.pop();
        if (d[state] != dist)
            continue;
        int p = state / n, v = state % n;
        if (!p) {
            if (v == goal) {
                cout << dist << '\n';
                return 0;
            }
            for (int jump : dogs[v]) {
                if (jump < B)
                    relax(jump * n + v, dist);
                else {
                    int cost = 1;
                    for (int u = v + jump; u < n; u += jump, cost++)
                        relax(u, dist + cost);
                    cost = 1;
                    for (int u = v - jump; u >= 0; u -= jump, cost++)
                        relax(u, dist + cost);
                }
            }
        } else {
            relax(v, dist);
            if (v + p < n)
                relax(p * n + v + p, dist + 1);
            if (v - p >= 0)
                relax(p * n + v - p, dist + 1);
        }
    }
    cout << -1 << '\n';

    return 0;
}
