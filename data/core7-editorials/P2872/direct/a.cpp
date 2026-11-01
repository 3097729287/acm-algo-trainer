#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];
vector<vector<char>>exists(n,vector<char>(n));for(int i=0;i<m;++i){int u,v;cin>>u>>v;--u;--v;exists[u][v]=exists[v][u]=true;}
const long long INF=(1LL<<62);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long double answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=sqrtl((long double)best[u]);
    for(int v=0;v<n;++v)if(!used[v]){long long dx=x[u]-x[v],dy=y[u]-y[v];long long w=exists[u][v]?0:dx*dx+dy*dy;best[v]=min(best[v],w);}
}cout<<fixed<<setprecision(2)<<answer<<'\n';
    return 0;
}
