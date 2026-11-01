#include <bits/stdc++.h>
using namespace std;

struct Edge { int type, u, v; };

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        cin >> n >> m;
        vector<Edge> edges(m);
        vector<vector<int>> graph(n);
        vector<int> indegree(n, 0);
        for (Edge &e : edges) {
            cin >> e.type >> e.u >> e.v;
            --e.u; --e.v;
            // 无向边尚未定向，不能参与入度或判环。
            if (e.type == 1) {
                graph[e.u].push_back(e.v);
                ++indegree[e.v];
            }
        }
        queue<int> q;
        for (int u = 0; u < n; ++u) if (indegree[u] == 0) q.push(u);
        vector<int> position(n, -1);
        int count = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            position[u] = count++;
            for (int v : graph[u]) if (--indegree[v] == 0) q.push(v);
        }
        if (count != n) { cout << "NO\n"; continue; }
        cout << "YES\n";
        for (Edge e : edges) {
            // 所有新增方向都沿拓扑序向后，因此不可能绕回起点。
            if (e.type == 0 && position[e.u] > position[e.v]) swap(e.u, e.v);
            cout << e.u + 1 << ' ' << e.v + 1 << '\n';
        }
    }
}
