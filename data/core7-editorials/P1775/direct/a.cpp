#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<long long> prefix(n+1);
for(int i=0,x;i<n;++i){cin>>x;prefix[i+1]=prefix[i]+x;}
vector<vector<long long>> dp(n,vector<long long>(n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1; dp[l][r]=LLONG_MAX/4;
        long long sum=prefix[r+1]-prefix[l];
        for(int k=l;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k+1][r]+sum);
    }
}
cout<<dp[0][n-1]<<'\n';
    return 0;
}
