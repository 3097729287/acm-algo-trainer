#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>a(n+1),count(m);for(int i=1;i<=n;++i){cin>>a[i];--a[i];++count[a[i]];}
vector<vector<int>>prefix(m,vector<int>(n+1));
for(int j=0;j<m;++j) for(int i=1;i<=n;++i) prefix[j][i]=prefix[j][i-1]+(a[i]==j);
int states=1<<m;vector<int>length(states),dp(states,n+1);dp[0]=0;
for(int mask=1;mask<states;++mask){int j=0;while(!(mask>>j&1)) ++j;length[mask]=length[mask^(1<<j)]+count[j];}
for(int mask=0;mask<states;++mask) for(int j=0;j<m;++j) if(!(mask>>j&1)){
    int left=length[mask],right=left+count[j];
    int displaced=count[j]-(prefix[j][right]-prefix[j][left]);
    dp[mask|(1<<j)]=min(dp[mask|(1<<j)],dp[mask]+displaced);
}
cout<<dp.back()<<'\n';
    return 0;
}
