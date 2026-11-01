#include <bits/stdc++.h>
using namespace std;
struct DSU{
    vector<int>parent,size;
    // 这里的n表示0至n-1共n个对象。
    explicit DSU(int n):parent(n),size(n,1){iota(parent.begin(),parent.end(),0);}
    int root(int u){while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;}
    bool merge(int u,int v){u=root(u);v=root(v);if(u==v)return false;
        if(size[u]<size[v])swap(u,v);parent[v]=u;size[u]+=size[v];return true;
    }
};
struct Edge{int u,v;long long w;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<char>has(n);for(int i=0,v;i<k;++i){cin>>v;has[v]=true;}
vector<Edge>edges(n-1);for(auto &e:edges)cin>>e.u>>e.v>>e.w;
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w>b.w;});DSU dsu(n);long long removed=0;
for(const auto &e:edges){int u=dsu.root(e.u),v=dsu.root(e.v);if(u==v)continue;
    if(has[u]&&has[v])removed+=e.w;
    else{bool occupied=has[u]||has[v];dsu.merge(u,v);has[dsu.root(u)]=occupied;}
}cout<<removed<<'\n';
    return 0;
}
