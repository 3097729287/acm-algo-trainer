#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int depth,n; cin>>depth>>n;
struct Trash{int time,food,height;};
vector<Trash> a(n);
for(auto &x:a) cin>>x.time>>x.food>>x.height;
sort(a.begin(),a.end(),[](const Trash &x,const Trash &y){return x.time<y.time;});
vector<int> dp(depth,-1); dp[0]=10;
for(auto x:a){
    auto next=dp;
    for(int h=0;h<depth;++h){
        if(dp[h]<x.time) continue; // 刚好等于落下时刻仍然能使用。
        if(h+x.height>=depth){cout<<x.time<<'\n';return 0;}
        next[h]=max(next[h],dp[h]+x.food); // 吃：只延长生命。
        next[h+x.height]=max(next[h+x.height],dp[h]); // 垫：只增加高度。
    }
    dp.swap(next);
}
cout<<dp[0]<<'\n';
    return 0;
}
