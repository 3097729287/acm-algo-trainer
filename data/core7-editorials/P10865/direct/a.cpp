#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,k;cin>>n>>m>>k;vector<int>x(k),y(k),fish(k);for(int i=0;i<k;++i) cin>>x[i]>>y[i]>>fish[i];
set<pair<int,int>>centers;int dx[5]={0,1,-1,0,0},dy[5]={0,0,0,1,-1};
for(int i=0;i<k;++i) for(int d=0;d<5;++d){int a=x[i]+dx[d],b=y[i]+dy[d];if(a>=1&&a<=n&&b>=1&&b<=m) centers.insert({a,b});}
set<int>unique;for(auto center:centers){int cover=0;for(int i=0;i<k;++i) if(abs(x[i]-center.first)+abs(y[i]-center.second)<=1) cover|=1<<(2*i);unique.insert(cover);}
vector<int>actions;for(int cover:unique) actions.push_back(cover);int lowBits=0,full=0;
for(int i=0;i<k;++i){lowBits|=1<<(2*i);full|=fish[i]<<(2*i);}
vector<int>dp(full+1,1000000000);dp[0]=0;
for(int state=1;state<=full;++state){
    int nonzero=(state|(state>>1))&lowBits;
    for(int cover:actions){int decrement=nonzero&cover;if(decrement) dp[state]=min(dp[state],1+dp[state-decrement]);}
}
cout<<dp[full]<<'\n';
    return 0;
}
