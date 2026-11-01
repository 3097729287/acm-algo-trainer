#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,limit; cin>>n>>limit;
vector<long long> a(n); for(auto &x:a) cin>>x;
vector<vector<vector<long long>>> dp(n,vector<vector<long long>>(n,vector<long long>(limit+1,-1)));
for(int i=0;i<n;++i) dp[i][i][0]=a[i];
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        for(int cut=l;cut<r;++cut){
            for(int x=0;x<=min(limit,cut-l);++x){
                for(int y=0;y<=min(limit,r-cut-1);++y){
                    long long left=dp[l][cut][x],right=dp[cut+1][r][y];
                    if(left<0||right<0) continue;
                    if(x+y<=limit) dp[l][r][x+y]=max(dp[l][r][x+y],left+right);
                    if(x+y+1<=limit) dp[l][r][x+y+1]=max(dp[l][r][x+y+1],left*right);
                }
            }
        }
    }
}
cout<<dp[0][n-1][limit]<<'\n';
    return 0;
}
