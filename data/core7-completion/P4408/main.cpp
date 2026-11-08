#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, long long>>> g(n);
    while (m--) {
        int a, b;
        long long w;
        cin >> a >> b >> w;
        a--;
        b--;
        g[a].push_back({b, w});
        g[b].push_back({a, w});
    }
    auto distances = [&](int s) {
        vector<long long> d(n, -1);
        vector<int> q = {s};
        d[s] = 0;
        for (int i = 0; i < (int)q.size(); i++)
            for (auto [u, w] : g[q[i]])
                if (d[u] < 0) {
                    d[u] = d[q[i]] + w;
                    q.push_back(u);
                }
        return d;
    };
    auto d = distances(0);
    int A = max_element(d.begin(), d.end()) - d.begin();
    auto x = distances(A);
    int B = max_element(x.begin(), x.end()) - x.begin();
    auto y = distances(B);
    long long extra = 0;
    for (int i = 0; i < n; i++)
        extra = max(extra, min(x[i], y[i]));
    cout << x[B] + extra << '\n';

    return 0;
}
