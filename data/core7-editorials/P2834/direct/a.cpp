#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,w;cin>>n>>w;const int MOD=1000000007;vector<int>dp(w+1);dp[0]=1;
for(int i=0,v;i<n;++i){cin>>v;for(int sum=v;sum<=w;++sum){dp[sum]+=dp[sum-v];if(dp[sum]>=MOD)dp[sum]-=MOD;}}
cout<<dp[w]<<'\n';
    return 0;
}
