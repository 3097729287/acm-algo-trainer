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
int n,W;cin>>n>>W;vector<Edge>forest;
for(int week=0;week<W;++week){Edge next;cin>>next.u>>next.v>>next.w;--next.u;--next.v;forest.push_back(next);
    sort(forest.begin(),forest.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);vector<Edge>chosen;long long total=0;
    for(const auto &e:forest)if(dsu.merge(e.u,e.v)){chosen.push_back(e);total+=e.w;}
    forest.swap(chosen);
    cout<<((int)forest.size()==n-1?total:-1)<<'\n';
}
    return 0;
}
