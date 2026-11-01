#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const long long MOD=1000000000;
string s;
while(cin>>s){
    int n=s.size();
    if(n%2==0){cout<<0<<'\n';continue;}
    vector<vector<long long>> dp(n,vector<long long>(n));
    for(int i=0;i<n;++i) dp[i][i]=1;
    for(int length=3;length<=n;length+=2){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1;
            if(s[l]!=s[r]) continue;
            for(int returned=l+2;returned<=r;returned+=2){
                if(s[returned]==s[l]) dp[l][r]=(dp[l][r]+dp[l+1][returned-1]*dp[returned][r])%MOD;
            }
        }
    }
    cout<<dp[0][n-1]<<'\n';
}
    return 0;
}
