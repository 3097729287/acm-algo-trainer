#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, s, t;
    cin >> n >> m >> s >> t;
    vector<vector<int>> graph(n + 1);
    vector<int> smallest(n + 1, n + 1);
    while (m--) {
        int a, b;
        cin >> a >> b;
        graph[a].push_back(b);
        smallest[a] = min(smallest[a], b);
    }
    const int INF = 1000000000;
    vector<int> distance(n + 1, INF);
    vector<bool> fixed(n + 1, false);
    deque<int> todo;
    distance[s] = 0;
    todo.push_front(s);
    while (!todo.empty()) {
        int u = todo.front();
        todo.pop_front();
        if (fixed[u]) continue;
        fixed[u] = true;
        for (int v : graph[u]) {
            int cost = (v == smallest[u] ? 0 : 1);
            if (distance[v] > distance[u] + cost) {
                distance[v] = distance[u] + cost;
                // 零费用留在当前层，费用为一的路线进入下一层。
                if (cost == 0) todo.push_front(v);
                else todo.push_back(v);
            }
        }
    }
    cout << (distance[t] == INF ? -1 : distance[t]) << '\n';
}
