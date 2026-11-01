#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,E;cin>>n>>E;const int ABSENT=1000000000;
vector<vector<int>>weight(n+1,vector<int>(n+1,ABSENT));
// 同端点的多份信息不能产生不同点序列。
for(int i=0;i<E;++i){int u,v,w;cin>>u>>v>>w;weight[u][v]=min(weight[u][v],w);}
const long long INF=(1LL<<60),CAP=(1LL<<30)+1;vector<long long>dist(n+1,INF),ways(n+1);vector<char>used(n+1);
dist[1]=0;ways[1]=1;
for(int step=0;step<n;++step){int u=-1;for(int v=1;v<=n;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    if(u==-1||dist[u]==INF)break;used[u]=true;
    for(int v=1;v<=n;++v)if(weight[u][v]!=ABSENT){long long candidate=dist[u]+weight[u][v];
        if(candidate<dist[v]){dist[v]=candidate;ways[v]=ways[u];}
        else if(candidate==dist[v])ways[v]=min(CAP,ways[v]+ways[u]);
    }
}if(dist[n]==INF)cout<<"No answer\n";else cout<<dist[n]<<' '<<ways[n]<<'\n';
    return 0;
}
