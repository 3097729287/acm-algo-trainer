#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,s,q;cin>>n>>m>>s>>q;vector<vector<pair<int,int>>>g(n+1);
for(int i=0;i<m;++i){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}
const long long INF=(1LL<<62);vector<long long>dist(n+1,INF);
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;// 堆条目保存这次入堆时的距离，旧条目稍后跳过。
dist[s]=0;pq.push({0,s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}while(q--){int home;cin>>home;cout<<dist[home]<<'\n';}
    return 0;
}
