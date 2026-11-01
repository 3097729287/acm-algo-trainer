#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; long long budget; cin>>n>>budget;
vector<int> attack(n); vector<long long> cost(n); int total=0;
for(int i=0;i<n;++i){cin>>attack[i]>>cost[i];total+=attack[i];}
const long long INF=LLONG_MAX/4;
vector<long long> dp(total+1,INF); dp[0]=0; int used=0;
for(int i=0;i<n;++i){
    used+=attack[i]; // 本轮最多只能达到已读道具的总攻击力。
    for(int sum=used;sum>=attack[i];--sum){
        if(dp[sum-attack[i]]!=INF){
            dp[sum]=min(dp[sum],dp[sum-attack[i]]+cost[i]);
        }
    }
}
for(int sum=total;sum>=0;--sum){
    if(dp[sum]<=budget){cout<<sum<<'\n';break;}
}
    return 0;
}
