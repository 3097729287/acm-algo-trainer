DIJKSTRA = r'''
vector<long long> dijkstra(const vector<vector<pair<int,long long>>> &graph, int source) {
    const long long inf = 1LL << 60;
    vector<long long> distance(graph.size(),inf);
    priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>> heap;
    distance[source] = 0; heap.push({0,source});
    while (!heap.empty()) {
        auto [cost,u] = heap.top(); heap.pop(); if (cost != distance[u]) continue;
        for (auto [v,w] : graph[u]) if (distance[v] > cost+w) {
            distance[v] = cost+w; heap.push({distance[v],v});
        }
    }
    return distance;
}
'''
SCC = r'''
pair<int,vector<int>> components(const vector<vector<int>> &graph, const vector<vector<int>> &reverse) {
    int n = graph.size(); vector<bool> seen(n); vector<int> finish;
    for (int start = 0; start < n; start++) if (!seen[start]) {
        vector<pair<int,int>> stack{{start,0}}; seen[start] = true;
        while (!stack.empty()) {
            int u = stack.back().first, &position = stack.back().second;
            if (position == (int)graph[u].size()) { finish.push_back(u); stack.pop_back(); }
            else { int v = graph[u][position++]; if (!seen[v]) { seen[v] = true; stack.push_back({v,0}); } }
        }
    }
    vector<int> component(n,-1); int count = 0;
    for (int i = n-1; i >= 0; i--) {
        int start = finish[i]; if (component[start] != -1) continue;
        vector<int> stack{start}; component[start] = count;
        while (!stack.empty()) { int u = stack.back(); stack.pop_back();
            for (int v : reverse[u]) if (component[v] == -1) { component[v] = count; stack.push_back(v); }
        }
        count++;
    }
    return {count,component};
}
'''
