#include <bits/stdc++.h>
using namespace std;
long long readHundredths(){
    // 原题保证正数且恰好两位小数，去掉小数点即为放大一百倍。
    string text;cin>>text;long long value=0;
    for(char c:text) if(c!='.') value=value*10+c-'0';
    return value;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;
while(tests--){
    int n,command;cin>>n>>command;vector<long long>x(n),y(n);
    for(int i=0;i<n;++i){x[i]=readHundredths();y[i]=readHundredths();}
    vector<vector<int>>cover(n,vector<int>(n));
    for(int i=0;i<n;++i){
        cover[i][i]=1<<i;
        for(int j=0;j<n;++j) if(x[i]!=x[j]){
            long long c=y[i]*x[j]-y[j]*x[i];
            if(c==0||((c>0)==(x[i]>x[j]))) continue;
            for(int k=0;k<n;++k){
                long long u=y[k]*x[i]-y[i]*x[k];
                if(u*x[j]*(x[i]-x[j])==c*x[k]*(x[k]-x[i])) cover[i][j]|=1<<k;
            }
        }
    }
    int states=1<<n;vector<int>dp(states,n);dp[0]=0;
    for(int mask=1;mask<states;++mask){
        int first=0;while(!(mask>>first&1)) ++first;
        for(int other=0;other<n;++other) if(cover[first][other]) dp[mask]=min(dp[mask],1+dp[mask&~cover[first][other]]);
    }
    cout<<dp.back()<<'\n';
}
    return 0;
}
