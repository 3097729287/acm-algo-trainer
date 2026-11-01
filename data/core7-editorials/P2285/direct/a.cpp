#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>t(m),x(m),y(m),dp(m,1);for(int i=0;i<m;++i)cin>>t[i]>>x[i]>>y[i];int answer=0;
for(int i=0;i<m;++i){for(int j=0;j<i;++j)if(t[i]-t[j]>=abs(x[i]-x[j])+abs(y[i]-y[j]))dp[i]=max(dp[i],dp[j]+1);answer=max(answer,dp[i]);}
cout<<answer<<'\n';
    return 0;
}
