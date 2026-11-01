#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,w;cin>>n>>w;vector<int>coin(n);for(int &v:coin)cin>>v;const int INF=1000000000;vector<int>dp(w+1,INF);dp[0]=0;
for(int sum=1;sum<=w;++sum)for(int v:coin)if(v<=sum&&dp[sum-v]!=INF)dp[sum]=min(dp[sum],dp[sum-v]+1);
cout<<dp[w]<<'\n';
    return 0;
}
