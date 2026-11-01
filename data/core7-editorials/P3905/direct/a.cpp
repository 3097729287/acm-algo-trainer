#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;const long long INF=(1LL<<60);
vector<vector<long long>>length(n+1,vector<long long>(n+1,INF)),cost=length;
for(int i=1;i<=n;++i)length[i][i]=cost[i][i]=0;
for(int i=0;i<m;++i){int u,v,w;cin>>u>>v>>w;length[u][v]=length[v][u]=w;cost[u][v]=cost[v][u]=0;}
// 完好路费用已经是零，只有损坏路恢复为修复长度。
int d;cin>>d;while(d--){int u,v;cin>>u>>v;cost[u][v]=cost[v][u]=length[u][v];}
int A,B;cin>>A>>B;vector<long long>dist(n+1,INF);vector<char>used(n+1);dist[A]=0;
for(int step=0;step<n;++step){int u=-1;for(int v=1;v<=n;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    if(u==-1||dist[u]==INF)break;used[u]=true;
    for(int v=1;v<=n;++v)if(cost[u][v]!=INF)dist[v]=min(dist[v],dist[u]+cost[u][v]);
}cout<<(dist[B]==INF?-1:dist[B])<<'\n';
    return 0;
}
