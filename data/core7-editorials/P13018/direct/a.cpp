#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<int> difference(n),value(n); int bound=0;
for(int i=0,a,b;i<n;++i){
    cin>>a>>b; difference[i]=a-b; value[i]=a+b; bound+=abs(difference[i]);
}
const int NEG=-1000000000;
vector<int> dp(2*bound+1,NEG); dp[bound]=0; // 下标bound表示差零。
for(int i=0;i<n;++i){
    auto next=dp;
    for(int index=0;index<(int)dp.size();++index){
        if(dp[index]==NEG) continue;
        int to=index+difference[i];
        if(to>=0&&to<(int)dp.size()) next[to]=max(next[to],dp[index]+value[i]);
    }
    dp.swap(next); // 读旧数组，正差、负差都不会重复使用当前食材。
}
cout<<dp[bound]<<'\n';
    return 0;
}
