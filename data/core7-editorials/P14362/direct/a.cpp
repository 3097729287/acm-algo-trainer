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
int n,m,k;cin>>n>>m>>k;vector<Edge>roads(m);for(auto &e:roads){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(roads.begin(),roads.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU original(n);
struct Candidate{int u,v;long long w;int bit;};vector<Candidate>edges;
for(const auto &e:roads)if(original.merge(e.u,e.v))edges.push_back({e.u,e.v,e.w,0});
vector<long long>activation(k);for(int j=0;j<k;++j){cin>>activation[j];for(int i=0;i<n;++i){long long w;cin>>w;edges.push_back({n+j,i,w,1<<j});}}
sort(edges.begin(),edges.end(),[](const Candidate &a,const Candidate &b){return a.w<b.w;});
long long answer=(1LL<<62);
for(int mask=0;mask<(1<<k);++mask){long long total=0;for(int j=0;j<k;++j)if(mask>>j&1)total+=activation[j];
    if(total>=answer)continue;int needed=n+__builtin_popcount((unsigned)mask)-1,selected=0;DSU dsu(n+k);
    if(needed==0){answer=min(answer,total);continue;}
    for(const auto &e:edges){if(e.bit&&!(mask&e.bit))continue;
        if(dsu.merge(e.u,e.v)){total+=e.w;++selected;if(selected==needed||total>=answer)break;}
    }
    if(selected==needed)answer=min(answer,total);
}cout<<answer<<'\n';
    return 0;
}
