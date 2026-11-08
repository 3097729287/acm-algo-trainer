#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int p;
        cin >> p;
        g[p - 1].push_back(i);
    }
    vector<long long> w(n), f(n);
    for (auto &x : w)
        cin >> x;
    for (int v = n - 1; v >= 0; v--) {
        sort(g[v].begin(), g[v].end(), [&](int a, int b) { return f[a] - w[a] > f[b] - w[b]; });
        long long saved = 0, best = 0;
        for (int u : g[v]) {
            best = max(best, saved + f[u]);
            saved += w[u];
        }
        f[v] = max(best, saved + w[v]);
    }
    for (int i = 0; i < n; i++)
        cout << f[i] << (i + 1 == n ? '\n' : ' ');

    return 0;
}
