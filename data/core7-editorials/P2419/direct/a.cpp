#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<bool>>reach(n+1,vector<bool>(n+1));
for(int i=0;i<m;++i){int u,v;cin>>u>>v;reach[u][v]=true;}
for(int k=1;k<=n;++k)for(int u=1;u<=n;++u)if(reach[u][k])
    for(int v=1;v<=n;++v)reach[u][v]=reach[u][v]||reach[k][v];
int answer=0;for(int u=1;u<=n;++u){bool fixed=true;for(int v=1;v<=n;++v)if(v!=u&&!reach[u][v]&&!reach[v][u])fixed=false;if(fixed)++answer;}
cout<<answer<<'\n';
    return 0;
}
