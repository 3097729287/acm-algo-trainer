TREE = r'''
struct Tree {
    vector<vector<pair<int,long long>>> edge;
    vector<int> parent, order;
    vector<long long> incoming;
    explicit Tree(int n) : edge(n), parent(n,-1), incoming(n) {}
    void add(int u, int v, long long w = 1) { edge[u].push_back({v,w}); edge[v].push_back({u,w}); }
    void root(int start) {
        order = {start}; parent[start] = start;
        for (size_t i = 0; i < order.size(); i++) {
            int u = order[i];
            for (auto [v,w] : edge[u]) if (v != parent[u]) { parent[v] = u; incoming[v] = w; order.push_back(v); }
        }
    }
};
'''
