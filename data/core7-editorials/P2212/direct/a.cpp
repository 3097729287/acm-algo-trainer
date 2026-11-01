#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long c;cin>>n>>c;vector<long long>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];
const long long INF=(1LL<<60);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long long answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    if(u==-1||best[u]==INF){cout<<-1<<'\n';return 0;}used[u]=true;answer+=best[u];
    for(int v=0;v<n;++v)if(!used[v]){long long dx=x[u]-x[v],dy=y[u]-y[v],w=dx*dx+dy*dy;
        if(w>=c)best[v]=min(best[v],w);
    }
}cout<<answer<<'\n';
    return 0;
}
