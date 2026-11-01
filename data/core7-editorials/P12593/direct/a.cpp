#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<long long>>weight(n,vector<long long>(n));
for(int i=0,u,v;i<m;++i){long long w;cin>>u>>v>>w;--u;--v;weight[u][v]=weight[v][u]=w;}
int states=1<<n;vector<long long>dp(states,LLONG_MAX/4);dp[0]=0;
for(int mask=1;mask<states;++mask){
    for(int u=0;u<n;++u) if(mask>>u&1){
        int count=0;long long sum=0;
        for(int v=0;v<n;++v) if((mask>>v&1)&&weight[u][v]){++count;sum+=weight[u][v];}
        dp[mask]=min(dp[mask],dp[mask^(1<<u)]+count*sum);
    }
}
cout<<dp.back()<<'\n';
    return 0;
}
