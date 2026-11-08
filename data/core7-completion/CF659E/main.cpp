#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> g(n);
    while (m--) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    vector<char> seen(n);
    int ans = 0;
    for (int s = 0; s < n; s++)
        if (!seen[s]) {
            long long edges = 0;
            int vertices = 0;
            vector<int> st = {s};
            seen[s] = 1;
            while (!st.empty()) {
                int v = st.back();
                st.pop_back();
                vertices++;
                edges += g[v].size();
                for (int u : g[v])
                    if (!seen[u]) {
                        seen[u] = 1;
                        st.push_back(u);
                    }
            }
            ans += edges / 2 == vertices - 1;
        }
    cout << ans << '\n';

    return 0;
}
