#include <bits/stdc++.h>
using namespace std;
struct DSU {
    vector<int>parent,size;
    DSU(int n):parent(n+1),size(n+1,1){iota(parent.begin(),parent.end(),0);}
    int find(int x){return parent[x]==x?x:parent[x]=find(parent[x]);}
    bool merge(int a,int b){
        a=find(a);b=find(b);if(a==b)return false;
        if(size[a]<size[b])swap(a,b);
        parent[b]=a;size[a]+=size[b];return true;
    }
};
struct Edge{int u,v;long long weight;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>cost(n+1);long long answer=LLONG_MAX;
for(int i=1;i<=n;++i){cin>>cost[i];answer=min(answer,cost[i]);}
vector<Edge>edges(m);for(auto &e:edges){long long length;cin>>e.u>>e.v>>length;e.weight=2*length+cost[e.u]+cost[e.v];}
sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.weight<b.weight;});
DSU groups(n);int chosen=0;for(auto e:edges)if(groups.merge(e.u,e.v)){answer+=e.weight;if(++chosen==n-1)break;}
cout<<answer<<'\n';
    return 0;
}
