#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k, d;
    cin >> n >> k >> d;
    vector<int> owner(n, -1), q;
    for (int i = 0; i < k; i++) {
        int p;
        cin >> p;
        p--;
        if (owner[p] < 0) {
            owner[p] = p;
            q.push_back(p);
        }
    }
    vector<vector<pair<int, int>>> g(n);
    vector<pair<int, int>> e;
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        e.push_back({a, b});
        g[a].push_back({b, i});
        g[b].push_back({a, i});
    }
    for (int i = 0; i < (int)q.size(); i++) {
        int v = q[i];
        for (auto [u, id] : g[v])
            if (owner[u] < 0) {
                owner[u] = owner[v];
                q.push_back(u);
            }
    }
    vector<int> cut;
    for (int i = 0; i < n - 1; i++)
        if (owner[e[i].first] != owner[e[i].second])
            cut.push_back(i + 1);
    cout << cut.size() << '\n';
    for (int i = 0; i < (int)cut.size(); i++)
        cout << cut[i] << (i + 1 == (int)cut.size() ? '\n' : ' ');
    if (cut.empty())
        cout << '\n';

    return 0;
}
