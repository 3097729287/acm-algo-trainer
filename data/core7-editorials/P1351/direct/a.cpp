#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<long long>w(n);for(auto &x:w)cin>>x;const int MOD=10007;long long maximum=0,total=0;
for(int u=0;u<n;++u){long long first=0,second=0,sum=0;
    for(int v:g[u]){total=(total+2*w[v]%MOD*sum)%MOD;sum=(sum+w[v])%MOD;
        if(w[v]>=first){second=first;first=w[v];}else second=max(second,w[v]);
    }maximum=max(maximum,first*second);
}cout<<maximum<<' '<<total<<'\n';
    return 0;
}
