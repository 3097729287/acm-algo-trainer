#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<long long>weight(n),sum(n);for(auto &x:weight) cin>>x;
vector<int>parent(n,-1),depth(n),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;depth[v]=depth[u]+1;order.push_back(v);}}
vector<vector<long long>>dp(n);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];sum[u]=weight[u];
    for(int v:g[u]) if(parent[v]==u) sum[u]+=sum[v];
    dp[u].resize(2*depth[u]+1);
    for(int d=-depth[u];d<=depth[u];++d){
        long long value=weight[u]*(1LL+d);
        for(int v:g[u]) if(parent[v]==u){
            long long same=dp[v][d+1+depth[v]];
            long long different=dp[v][-d+depth[v]]+1LL*d*sum[v];
            value+=max(same,different);
        }
        dp[u][d+depth[u]]=value;
    }
}
cout<<dp[0][0]<<'\n';
    return 0;
}
