#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<long long> original(n); for(auto &x:original) cin>>x;
vector<long long> a(2*n+1);
for(int i=0;i<=2*n;++i) a[i]=original[i%n];
vector<vector<long long>> dp(2*n,vector<long long>(2*n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=2*n;++l){
        int r=l+length-1;
        for(int k=l;k<r;++k){
            dp[l][r]=max(dp[l][r],dp[l][k]+dp[k+1][r]+a[l]*a[k+1]*a[r+1]);
        }
    }
}
long long answer=0;
for(int start=0;start<n;++start) answer=max(answer,dp[start][start+n-1]);
cout<<answer<<'\n';
    return 0;
}
