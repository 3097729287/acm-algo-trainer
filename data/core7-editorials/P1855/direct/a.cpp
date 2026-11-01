#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,t; cin>>n>>m>>t;
vector<vector<int>> dp(m+1,vector<int>(t+1));
for(int i=0,cost,duration;i<n;++i){
    cin>>cost>>duration;
    // 两种容量都倒序；即便两种消耗都是零，每格也只加一次。
    for(int money=m;money>=cost;--money){
        for(int time=t;time>=duration;--time){
            dp[money][time]=max(dp[money][time],dp[money-cost][time-duration]+1);
        }
    }
}
cout<<dp[m][t]<<'\n';
    return 0;
}
