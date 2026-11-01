#include <bits/stdc++.h>
using namespace std;
int farthest(int start, const vector<vector<int>> &g, vector<int> &dist, vector<int> &parent) {
    int n = g.size();
    dist.assign(n, -1); parent.assign(n, -1);
    queue<int> q;
    q.push(start); dist[start] = 0;
    int best = start;
    while (!q.empty()) {
        int v = q.front(); q.pop();
        if (dist[v] > dist[best]) best = v;
        for (int u : g[v]) if (dist[u] == -1) {
            dist[u] = dist[v] + 1; parent[u] = v; q.push(u);
        }
    }
    return best;
}
vector<int> endpoint_colors(int root, int blocked, int depth, int target,
                            const vector<vector<int>> &g, const vector<int> &color) {
    vector<int> result;
    vector<array<int, 3>> st = {{root, blocked, depth}};
    while (!st.empty()) {
        auto item = st.back(); st.pop_back();
        int v = item[0], parent = item[1], d = item[2];
        if (d == target) { result.push_back(color[v]); continue; }
        for (int u : g[v]) if (u != parent) st.push_back({u, v, d + 1});
    }
    return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<vector<int>> g(n);
    for (int i = 1, u, v; i < n; ++i) { cin >> u >> v; --u; --v; g[u].push_back(v); g[v].push_back(u); }
    vector<int> color(n);
    for (int &c : color) cin >> c;
    vector<int> dist, parent;
    int a = farthest(0, g, dist, parent);
    int b = farthest(a, g, dist, parent);
    int diameter = dist[b], radius = diameter / 2;
    vector<int> path;
    for (int v = b; v != -1; v = parent[v]) path.push_back(v);
    vector<long long> seen(n + 1);
    long long answer = 0;
    if (diameter % 2 == 1) {
        int left = path[radius], right = path[radius + 1];
        for (int c : endpoint_colors(left, right, 0, radius, g, color)) ++seen[c];
        for (int c : endpoint_colors(right, left, 0, radius, g, color)) answer += seen[c];
    } else {
        int center = path[radius];
        for (int u : g[center]) {
            vector<int> group = endpoint_colors(u, center, 1, radius, g, color);
            // 当前分支只与先前分支配对，避免同分支误计。
            for (int c : group) answer += seen[c];
            for (int c : group) ++seen[c];
        }
    }
    cout << answer << '\n';
}
