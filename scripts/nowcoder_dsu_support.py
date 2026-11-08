DSU = r'''
struct DSU {
    vector<int> parent, size;
    DSU(int n) : parent(n + 1), size(n + 1, 1) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; }
        return x;
    }
    bool unite(int a, int b) {
        a = find(a); b = find(b); if (a == b) return false;
        if (size[a] < size[b]) swap(a,b);
        parent[b] = a; size[a] += size[b]; return true;
    }
};
'''
