#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<vector<pair<int,long long>>>g(n+k+1);
// 集合 i 的中转点为 n+i，一份成员信息仅建两条邻接记录。
for(int i=1;i<=k;++i){int size;cin>>size;while(size--){int u;long long w;cin>>u>>w;g[u].push_back({n+i,w});g[n+i].push_back({u,w});}}
const long long INF=4557430888798830399LL;vector<long long>dist(n+k+1,INF);
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;dist[1]=0;pq.push({0,1});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}for(int u=1;u<=n;++u)cout<<dist[u]<<(u==n?'\n':' ');
    return 0;
}
