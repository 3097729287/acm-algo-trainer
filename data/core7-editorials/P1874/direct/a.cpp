#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string text;int target;cin>>text>>target;int length=text.size();const int INF=1000000000;
vector<vector<int>>dp(length+1,vector<int>(target+1,INF));dp[0][0]=0;
for(int i=0;i<length;++i)for(int sum=0;sum<=target;++sum)if(dp[i][sum]!=INF){int value=0;
    for(int j=i;j<length;++j){value=value*10+(text[j]-'0');if(value>target)break;if(sum+value<=target)dp[j+1][sum+value]=min(dp[j+1][sum+value],dp[i][sum]+1);}
}cout<<(dp[length][target]==INF?-1:dp[length][target]-1)<<'\n';
    return 0;
}
