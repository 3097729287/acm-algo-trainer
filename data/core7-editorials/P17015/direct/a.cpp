#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<long long> a(n+2); for(int i=1;i<=n;++i) cin>>a[i];
vector<vector<long long>> dp(n+2,vector<long long>(n+2));
for(int length=1;length<=n;++length){
    for(int l=1;l+length-1<=n;++l){
        int r=l+length-1;
        for(int k=l;k<=r;++k){
            // k最后删，它自己的值不计分。
            dp[l][r]=max(dp[l][r],dp[l][k-1]+dp[k+1][r]+a[l-1]+a[r+1]);
        }
    }
}
cout<<dp[1][n]<<'\n';
    return 0;
}
