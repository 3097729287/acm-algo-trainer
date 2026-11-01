#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m; cin>>m;
vector<int> power;
for(long long i=1;i*i*i*i<=m;++i) power.push_back(i*i*i*i);
vector<int> dp(m+1,m+1); dp[0]=0;
// 枚举最后一项，所依赖的更小和已经算好。
for(int sum=1;sum<=m;++sum){
    for(int v:power){
        if(v>sum) break;
        dp[sum]=min(dp[sum],dp[sum-v]+1);
    }
}
cout<<dp[m]<<'\n';
    return 0;
}
