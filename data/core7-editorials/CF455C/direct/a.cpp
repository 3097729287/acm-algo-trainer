#include <bits/stdc++.h>
using namespace std;
struct DSU{vector<int>p,size;explicit DSU(int n):p(n),size(n,1){iota(p.begin(),p.end(),0);}int root(int u){while(p[u]!=u){p[u]=p[p[u]];u=p[u];}return u;}bool merge(int a,int b){a=root(a);b=root(b);if(a==b)return false;if(size[a]<size[b])swap(a,b);p[b]=a;size[a]+=size[b];return true;}};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,q;cin>>n>>m>>q;vector<vector<int>>g(n);DSU dsu(n);
for(int i=0,u,v;i<m;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);dsu.merge(u,v);}
vector<int>diameter(n),parent(n),dist(n);vector<char>seen(n);
auto farthest=[&](int s){vector<int>order{s};parent[s]=s;dist[s]=0;int best=s;
    for(size_t i=0;i<order.size();++i){int u=order[i];seen[u]=true;if(dist[u]>dist[best])best=u;
        for(int v:g[u])if(v!=parent[u]){parent[v]=u;dist[v]=dist[u]+1;order.push_back(v);}}
    return best;
};for(int u=0;u<n;++u)if(!seen[u]){int a=farthest(u),b=farthest(a);diameter[dsu.root(u)]=dist[b];}
while(q--){int type,x,y;cin>>type>>x;--x;int a=dsu.root(x);if(type==1){cout<<diameter[a]<<'\n';continue;}
    cin>>y;int b=dsu.root(y-1);if(a==b)continue;
    int value=max({diameter[a],diameter[b],(diameter[a]+1)/2+(diameter[b]+1)/2+1});
    dsu.merge(a,b);diameter[dsu.root(a)]=value;
}
    return 0;
}
