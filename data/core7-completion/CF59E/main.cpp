#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;
    vector<vector<int>> g(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    unordered_set<long long> bad;
    auto key = [&](int a, int b, int c) { return (1LL * a * n + b) * n + c; };
    while (k--) {
        int a, b, c;
        cin >> a >> b >> c;
        bad.insert(key(a - 1, b - 1, c - 1));
    }
    vector<int> parent((n + 1) * n, -2), q = {n * n};
    parent[n * n] = -1;
    int goal = -1;
    for (int i = 0; i < (int)q.size(); i++) {
        int state = q[i], pre = state / n, v = state % n;
        if (v == n - 1) {
            goal = state;
            break;
        }
        for (int u : g[v])
            if (!bad.count(key(pre, v, u))) {
                int next = v * n + u;
                if (parent[next] == -2) {
                    parent[next] = state;
                    q.push_back(next);
                }
            }
    }
    if (goal < 0) {
        cout << -1 << '\n';
        return 0;
    }
    vector<int> path;
    for (int s = goal; s >= 0; s = parent[s])
        path.push_back(s % n + 1);
    reverse(path.begin(), path.end());
    cout << path.size() - 1 << '\n';
    for (int i = 0; i < (int)path.size(); i++)
        cout << path[i] << (i + 1 == (int)path.size() ? '\n' : ' ');

    return 0;
}
