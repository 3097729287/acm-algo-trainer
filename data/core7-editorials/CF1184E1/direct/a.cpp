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
int n,m;cin>>n>>m;int a,b;long long ignored;cin>>a>>b>>ignored;--a;--b;vector<Edge>edges(m-1);
for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(edges.begin(),edges.end(),[](const Edge &x,const Edge &y){return x.w<y.w;});DSU dsu(n);long long answer=1000000000;
for(const auto &e:edges){dsu.merge(e.u,e.v);if(dsu.root(a)==dsu.root(b)){answer=e.w;break;}}
cout<<answer<<'\n';
    return 0;
}
