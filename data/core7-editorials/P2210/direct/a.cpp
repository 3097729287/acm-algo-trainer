#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>friends(n,vector<int>(3));
for(auto &row:friends) for(int &v:row){cin>>v;--v;}
int states=1<<n;vector<int>cut(states),dp(states,1000000000);dp[0]=0;
for(int mask=1;mask<states;++mask){
    int v=0;while(!(mask>>v&1)) ++v;int rest=mask^(1<<v),inside=0;
    for(int u:friends[v]) if(rest>>u&1) ++inside;
    cut[mask]=cut[rest]+3-2*inside;
}
for(int mask=1;mask<states;++mask) for(int v=0;v<n;++v) if(mask>>v&1) dp[mask]=min(dp[mask],dp[mask^(1<<v)]+cut[mask]);
cout<<dp.back()<<'\n';
    return 0;
}
