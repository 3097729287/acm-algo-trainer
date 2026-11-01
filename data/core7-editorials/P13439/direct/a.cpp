#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests; cin>>tests;
for(int test=1;test<=tests;++test){
    int cells,q; cin>>cells>>q; vector<int>pos(q+2); pos[q+1]=cells+1;
    for(int i=1;i<=q;++i) cin>>pos[i];
    vector<vector<int>>dp(q+2,vector<int>(q+2));
    for(int gap=2;gap<=q+1;++gap){
        for(int l=0;l+gap<=q+1;++l){
            int r=l+gap; dp[l][r]=INT_MAX/4;
            for(int k=l+1;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k][r]+pos[r]-pos[l]-2);
        }
    }
    cout<<"Case #"<<test<<": "<<dp[0][q+1]<<'\n';
}
    return 0;
}
