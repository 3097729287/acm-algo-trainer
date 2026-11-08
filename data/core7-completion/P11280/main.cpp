#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, r;
    cin >> n >> m >> r;
    r--;
    vector<vector<int>> g(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    vector<int> d(n, -1), q = {r};
    d[r] = 0;
    for (int i = 0; i < (int)q.size(); i++)
        for (int u : g[q[i]])
            if (d[u] < 0) {
                d[u] = d[q[i]] + 1;
                q.push_back(u);
            }
    cout << "I'm here!\n";
    int Q;
    cin >> Q;
    while (Q--) {
        int a, b;
        cin >> a >> b;
        cout << (d[a - 1] <= d[b - 1] ? "Terry" : "Jom") << '\n';
    }

    return 0;
}
