#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int length;
while(cin>>length&&length){
    int n; cin>>n; vector<int> pos(n+2); pos[n+1]=length;
    for(int i=1;i<=n;++i) cin>>pos[i];
    vector<vector<int>> dp(n+2,vector<int>(n+2));
    for(int gap=2;gap<=n+1;++gap){
        for(int l=0;l+gap<=n+1;++l){
            int r=l+gap; dp[l][r]=INT_MAX/4;
            for(int k=l+1;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k][r]+pos[r]-pos[l]);
        }
    }
    cout<<"The minimum cutting is "<<dp[0][n+1]<<".\n";
}
    return 0;
}
