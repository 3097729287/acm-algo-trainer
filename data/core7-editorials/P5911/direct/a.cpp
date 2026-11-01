#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int capacity,n;cin>>capacity>>n;vector<int>time(n),weight(n);for(int i=0;i<n;++i) cin>>time[i]>>weight[i];
int states=1<<n;vector<int>sum(states),slowest(states),dp(states,1000000000);dp[0]=0;
for(int mask=1;mask<states;++mask){
    int v=0;while(!(mask>>v&1)) ++v;int rest=mask^(1<<v);
    sum[mask]=sum[rest]+weight[v];slowest[mask]=max(slowest[rest],time[v]);
}
for(int mask=1;mask<states;++mask){
    int anchor=mask&-mask;
    for(int group=mask;group;group=(group-1)&mask) if((group&anchor)&&sum[group]<=capacity) dp[mask]=min(dp[mask],dp[mask^group]+slowest[group]);
}
cout<<dp.back()<<'\n';
    return 0;
}
