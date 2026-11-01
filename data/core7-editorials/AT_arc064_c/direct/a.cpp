#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long double sx,sy,tx,ty;cin>>sx>>sy>>tx>>ty;int n;cin>>n;
vector<long double>x(n+2),y(n+2),radius(n+2);x[0]=sx;y[0]=sy;x[n+1]=tx;y[n+1]=ty;
for(int i=1;i<=n;++i)cin>>x[i]>>y[i]>>radius[i];
const long double INF=1e100L;vector<long double>dist(n+2,INF);vector<char>used(n+2);dist[0]=0;
for(int step=0;step<n+2;++step){int u=-1;for(int v=0;v<n+2;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    used[u]=true;for(int v=0;v<n+2;++v){
        // 重叠或包含时不存在暴露间隙。
        long double gap=max(0.0L,hypotl(x[u]-x[v],y[u]-y[v])-radius[u]-radius[v]);
        dist[v]=min(dist[v],dist[u]+gap);
    }
}cout<<fixed<<setprecision(18)<<dist[n+1]<<'\n';
    return 0;
}
