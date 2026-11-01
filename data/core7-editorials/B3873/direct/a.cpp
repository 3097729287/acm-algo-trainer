#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,l; cin>>n>>l;
const long long INF=LLONG_MAX/4;
vector<long long> dp(l+1,INF); dp[0]=0;
for(int i=0,cost,volume;i<n;++i){
    cin>>cost>>volume;
    auto next=dp; // 先保留不买，只读取未含本瓶的旧数组。
    for(int v=0;v<=l;++v){
        if(dp[v]==INF) continue;
        int to=min(l,v+volume); // 所有已达标容量合并。
        next[to]=min(next[to],dp[v]+cost);
    }
    dp.swap(next);
}
if(dp[l]==INF) cout<<"no solution\n";
else cout<<dp[l]<<'\n';
    return 0;
}
