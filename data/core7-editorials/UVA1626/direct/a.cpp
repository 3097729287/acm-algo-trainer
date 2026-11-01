#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests; cin>>tests; string s,line;
getline(cin,line); getline(cin,line); // 行尾与首个案例前的分隔空行。
for(int test=0;test<tests;++test){
    getline(cin,s); int n=s.size();
    vector<vector<int>> dp(n,vector<int>(n));
    auto match=[](char a,char b){return (a=='('&&b==')')||(a=='['&&b==']');};
    for(int i=0;i<n;++i) dp[i][i]=1;
    for(int length=2;length<=n;++length){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1; dp[l][r]=n+1;
            if(match(s[l],s[r])) dp[l][r]=length==2?0:dp[l+1][r-1];
            for(int k=l;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k+1][r]);
        }
    }
    function<void(int,int)> emit=[&](int l,int r){
        if(l>r) return;
        if(l==r){cout<<((s[l]=='('||s[l]==')')?"()":"[]");return;}
        int inside=r-l==1?0:dp[l+1][r-1];
        if(match(s[l],s[r])&&dp[l][r]==inside){cout<<s[l];emit(l+1,r-1);cout<<s[r];return;}
        for(int k=l;k<r;++k){
            if(dp[l][r]==dp[l][k]+dp[k+1][r]){emit(l,k);emit(k+1,r);return;}
        }
    };
    if(test) cout<<'\n';
    emit(0,n-1); cout<<'\n';
    if(test+1<tests) getline(cin,line); // 只消费案例间的一个分隔行。
}
    return 0;
}
