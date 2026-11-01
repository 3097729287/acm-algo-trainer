#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int k,n; cin>>k>>n;
vector<int> coin(n); for(int &x:coin) cin>>x;
sort(coin.begin(),coin.end());
int bound=k*coin.back();
vector<int> dp(bound+1,k+1); dp[0]=0;
for(int sum=1;sum<=bound;++sum){
    for(int v:coin){
        if(v>sum) break;
        dp[sum]=min(dp[sum],dp[sum-v]+1);
    }
    // 连续覆盖不能跨过缺口，立即结束。
    if(dp[sum]>k){cout<<sum-1<<'\n';return 0;}
}
cout<<bound<<'\n';
    return 0;
}
