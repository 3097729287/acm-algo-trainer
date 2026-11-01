#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<int> a(n),prefix(n+1);
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i){cin>>a[i];prefix[i+1]=prefix[i]+a[i];dp[i][i]=a[i];}
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        dp[l][r]=prefix[r+1]-prefix[l]-min(dp[l+1][r],dp[l][r-1]);
    }
}
cout<<dp[0][n-1]<<' '<<prefix[n]-dp[0][n-1]<<'\n';
    return 0;
}
