#include <bits/stdc++.h>
using namespace std;
struct Edge{int u,v;long long w;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<Edge>edges(m);vector<vector<pair<int,int>>>g(n);
for(int i=0;i<m;++i){auto &e=edges[i];cin>>e.u>>e.v>>e.w;--e.u;--e.v;g[e.u].push_back({e.v,i});g[e.v].push_back({e.u,i});}
int s;cin>>s;--s;const long long INF=(1LL<<62);vector<long long>dist(n,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[s]=0;pq.push({0,s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,index]:g[u])if(du+edges[index].w<dist[v]){dist[v]=du+edges[index].w;pq.push({dist[v],v});}
}
vector<long long>cost(n,INF);vector<int>parentEdge(n,-1);
for(int i=0;i<m;++i){const auto &e=edges[i];
    if(dist[e.u]+e.w==dist[e.v]&&e.w<cost[e.v]){cost[e.v]=e.w;parentEdge[e.v]=i;}
    if(dist[e.v]+e.w==dist[e.u]&&e.w<cost[e.u]){cost[e.u]=e.w;parentEdge[e.u]=i;}
}long long answer=0;for(int v=0;v<n;++v)if(v!=s)answer+=cost[v];cout<<answer<<'\n';
for(int v=0;v<n;++v)if(v!=s)cout<<parentEdge[v]+1<<' ';cout<<'\n';
    return 0;
}
