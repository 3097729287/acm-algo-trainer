#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<vector<int>>task(n+1);for(int i=0,p,t;i<k;++i){cin>>p>>t;task[p].push_back(t);}
vector<int>dp(n+2);for(int t=n;t>=1;--t){if(task[t].empty())dp[t]=dp[t+1]+1;else for(int duration:task[t])dp[t]=max(dp[t],dp[t+duration]);}
cout<<dp[1]<<'\n';
    return 0;
}
