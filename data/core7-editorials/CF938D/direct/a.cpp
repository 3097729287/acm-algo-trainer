#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<pair<int,long long>>>g(n+1);
for(int i=0;i<m;++i){int u,v;long long w;cin>>u>>v>>w;g[u].push_back({v,2*w});g[v].push_back({u,2*w});}
vector<long long>dist(n+1);using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;
// 所有城市同时作为带有各自初始票价的源。
for(int i=1;i<=n;++i){cin>>dist[i];pq.push({dist[i],i});}
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}for(int i=1;i<=n;++i)cout<<dist[i]<<(i==n?'\n':' ');
    return 0;
}
