#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> x(n), y(n);
    for (int i = 0; i < n; ++i) cin >> x[i] >> y[i];
    vector<bool> seen(n, false);
    int components = 0;
    for (int s = 0; s < n; ++s) {
        if (seen[s]) continue;
        ++components;
        queue<int> q;
        q.push(s);
        seen[s] = true;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v = 0; v < n; ++v) {
                if (!seen[v] && (x[u] == x[v] || y[u] == y[v])) {
                    seen[v] = true;  // 入队时标记，避免重复加入。
                    q.push(v);
                }
            }
        }
    }
    cout << components - 1 << '\n';
}
