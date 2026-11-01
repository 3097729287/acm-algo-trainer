#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,k;cin>>n>>m>>k;const int INF=1000000000;vector<int>dp(k+1,INF);dp[0]=0;
for(int day=0;day<n;++day){string row;cin>>row;vector<int>p;for(int j=0;j<m;++j)if(row[j]=='1')p.push_back(j);int c=p.size(),limit=min(c,k);vector<int>cost(limit+1,INF);
    for(int removed=0;removed<=limit;++removed){int remain=c-removed;if(remain==0){cost[removed]=0;continue;}
        for(int l=0;l+remain<=c;++l)cost[removed]=min(cost[removed],p[l+remain-1]-p[l]+1);
    }vector<int>next(k+1,INF);
    for(int used=0;used<=k;++used)if(dp[used]!=INF)for(int removed=0;removed<=limit&&used+removed<=k;++removed)next[used+removed]=min(next[used+removed],dp[used]+cost[removed]);
    dp.swap(next);
}cout<<*min_element(dp.begin(),dp.end())<<'\n';
    return 0;
}
