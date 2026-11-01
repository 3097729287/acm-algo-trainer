#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>fixedColor(n,-1);bool conflict=false;
for(int i=0,u,c;i<k;++i){cin>>u>>c;--u;--c;if(fixedColor[u]>=0&&fixedColor[u]!=c) conflict=true;fixedColor[u]=c;}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
const long long MOD=1000000007;
vector<vector<long long>>dp(n,vector<long long>(3));
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];
    for(int c=0;c<3;++c){
        if(fixedColor[u]>=0&&fixedColor[u]!=c) continue;
        dp[u][c]=1;
        for(int v:g[u]) if(parent[v]==u){
            long long ways=0;for(int other=0;other<3;++other) if(other!=c) ways+=dp[v][other];
            dp[u][c]=dp[u][c]*(ways%MOD)%MOD;
        }
    }
}
cout<<(conflict?0:(dp[0][0]+dp[0][1]+dp[0][2])%MOD)<<'\n';
    return 0;
}
