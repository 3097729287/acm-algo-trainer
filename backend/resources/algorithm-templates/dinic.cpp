#include <bits/stdc++.h>
#include <cassert>
using namespace std;

// 顶点 [0,n)，容量非负；总流量在 long long 范围内。路径显式保存，避免深图递归。
struct Dinic {
    struct Edge { int to, rev; long long cap; };
    vector<vector<Edge>> g;
    vector<int> level, current;
    explicit Dinic(int n) : g(n), level(n), current(n) {}
    void add_edge(int u, int v, long long capacity) {
        assert(0 <= u && u < (int)g.size() && 0 <= v && v < (int)g.size() && capacity >= 0);
        int a = g[u].size(), b = g[v].size();
        // 自环的正反向边都放在同一个 vector 中，反向下标须额外 +1。
        g[u].push_back({v, b + (u == v), capacity});
        g[v].push_back({u, a, 0});
    }
    bool bfs(int s, int t) {
        fill(level.begin(), level.end(), -1);
        queue<int> q; q.push(s); level[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (auto e : g[u]) if (e.cap > 0 && level[e.to] < 0) {
                level[e.to] = level[u] + 1; q.push(e.to);
            }
        }
        return level[t] >= 0;
    }
    long long augment(int s, int t, long long limit) {
        vector<pair<int,int>> path;
        int u = s;
        while (true) {
            if (u == t) {
                long long pushed = limit;
                for (auto [v,i] : path) pushed = min(pushed, g[v][i].cap);
                for (auto [v,i] : path) {
                    auto& e = g[v][i]; e.cap -= pushed; g[e.to][e.rev].cap += pushed;
                }
                return pushed;
            }
            int& i = current[u];
            while (i < (int)g[u].size() && !(g[u][i].cap > 0 && level[g[u][i].to] == level[u] + 1)) ++i;
            if (i < (int)g[u].size()) { path.push_back({u,i}); u = g[u][i].to; }
            else {
                level[u] = -1;
                if (path.empty()) return 0;
                u = path.back().first; path.pop_back(); ++current[u];
            }
        }
    }
    // 在现有残量网络继续增广，返回本次新增流量。s=t 时约定为 0。
    long long max_flow(int s, int t) {
        assert(0 <= s && s < (int)g.size() && 0 <= t && t < (int)g.size());
        if (s == t) return 0;
        long long flow = 0;
        while (bfs(s,t)) {
            fill(current.begin(), current.end(), 0);
            while (long long f = augment(s,t,LLONG_MAX-flow)) {
                flow += f;
                if (flow == LLONG_MAX) return flow;
            }
        }
        return flow;
    }
    // 完整最大流结束后，从源点可经正残量到达的点构成最小割源侧。
    vector<bool> source_side(int s) const {
        vector<bool> seen(g.size()); queue<int> q; q.push(s); seen[s] = true;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (auto e : g[u]) if (e.cap > 0 && !seen[e.to]) { seen[e.to] = true; q.push(e.to); }
        }
        return seen;
    }
};
