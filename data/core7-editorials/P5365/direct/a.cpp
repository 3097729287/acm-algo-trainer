#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; long long target; cin>>n>>target;
vector<int> k(n),cost(n);
for(int &x:k) cin>>x;
for(int &x:cost) cin>>x;
if(target<=1){cout<<0<<'\n';return 0;}
// 先取得可行费用上界，随后仍对全部英雄做最优化。
int bound=0; long long product=1;
for(int i=0;i<n&&product<target;++i){
    if(k[i]>1){bound+=k[i]*cost[i];product=min(target,product*k[i]);}
}
vector<long long> dp(bound+1); dp[0]=1;
for(int i=0;i<n;++i){
    auto next=dp; // 不买；购买一款被不买支配。
    for(int used=0;used<=bound;++used){
        if(!dp[used]) continue;
        for(int buy=2;buy<=k[i]&&used+buy*cost[i]<=bound;++buy){
            int to=used+buy*cost[i];
            next[to]=max(next[to],min(target,dp[used]*buy));
        }
    }
    dp.swap(next);
}
for(int used=0;used<=bound;++used){
    if(dp[used]>=target){cout<<used<<'\n';break;}
}
    return 0;
}
