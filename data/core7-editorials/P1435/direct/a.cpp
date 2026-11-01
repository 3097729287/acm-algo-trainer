#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; cin>>s; int n=s.size();
vector<vector<int>> dp(n,vector<int>(n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(s[l]==s[r]) dp[l][r]=length==2?0:dp[l+1][r-1];
        else dp[l][r]=1+min(dp[l+1][r],dp[l][r-1]);
    }
}
cout<<dp[0][n-1]<<'\n';
    return 0;
}
