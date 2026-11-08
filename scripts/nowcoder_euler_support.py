EULER = r'''
struct EulerTree {
    int n; vector<vector<int>> edge;
    vector<int> parent,depth,in,out,order;
    EulerTree(int n):n(n),edge(n+1),parent(n+1),depth(n+1),in(n+1),out(n+1) {}
    void add(int u,int v) { edge[u].push_back(v); edge[v].push_back(u); }
    void root(int start) {
        vector<int> stack={start}; parent[start]=0; order.clear();
        while (!stack.empty()) {
            int u=stack.back(); stack.pop_back(); in[u]=order.size()+1; order.push_back(u);
            for (int v:edge[u]) if (v!=parent[u]) { parent[v]=u; depth[v]=depth[u]+1; stack.push_back(v); }
        }
        vector<int> size(n+1,1);
        for (int i=(int)order.size()-1;i>=0;i--) { int u=order[i]; out[u]=in[u]+size[u]-1; if (parent[u]) size[parent[u]]+=size[u]; }
    }
};
'''
LCA = r'''
struct Ancestors {
    const EulerTree &tree; vector<vector<int>> up;
    Ancestors(const EulerTree &tree):tree(tree) {
        int levels=1; while ((1LL<<levels)<=tree.n) levels++;
        up.assign(levels,vector<int>(tree.n+1)); up[0]=tree.parent;
        for (int b=1;b<levels;b++) for (int u=1;u<=tree.n;u++) up[b][u]=up[b-1][up[b-1][u]];
    }
    int lca(int u,int v) const {
        if (tree.depth[u]<tree.depth[v]) swap(u,v);
        int gap=tree.depth[u]-tree.depth[v];
        for (int b=0;b<(int)up.size();b++) if (gap>>b&1) u=up[b][u];
        if (u==v) return u;
        for (int b=(int)up.size()-1;b>=0;b--) if (up[b][u]!=up[b][v]) { u=up[b][u]; v=up[b][v]; }
        return up[0][u];
    }
    int distance(int u,int v) const { return tree.depth[u]+tree.depth[v]-2*tree.depth[lca(u,v)]; }
};
'''
