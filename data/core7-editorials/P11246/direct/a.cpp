#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<int> dp(n+1,n+1); dp[0]=0;
for(int sum=1;sum<=n;++sum){
    // 不限制旧状态用过什么底数，因此同一平方可重复。
    for(int j=1;j*j<=sum;++j) dp[sum]=min(dp[sum],dp[sum-j*j]+1);
}
cout<<dp[n]<<'\n';
    return 0;
}
