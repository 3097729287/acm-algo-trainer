#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;const int MOD=1000007;vector<int>dp(m+1);dp[0]=1;
for(int i=0,limit;i<n;++i){cin>>limit;vector<int>next(m+1);
    for(int amount=0;amount<=m;++amount)for(int count=0;count<=limit&&count<=amount;++count){next[amount]+=dp[amount-count];if(next[amount]>=MOD)next[amount]-=MOD;}
    dp.swap(next);
}cout<<dp[m]<<'\n';
    return 0;
}
