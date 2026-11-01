#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s,t; cin>>s>>t; int n=s.size(),m=t.size();
const int MOD=998244353;
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i) if(i>=m||s[0]==t[i]) dp[i][i]=2;
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(l>=m||s[length-1]==t[l]) dp[l][r]+=dp[l+1][r];
        if(r>=m||s[length-1]==t[r]) dp[l][r]+=dp[l][r-1];
        if(dp[l][r]>=MOD) dp[l][r]-=MOD;
    }
}
int answer=0;
for(int length=m;length<=n;++length){answer+=dp[0][length-1];if(answer>=MOD) answer-=MOD;}
cout<<answer<<'\n';
    return 0;
}
