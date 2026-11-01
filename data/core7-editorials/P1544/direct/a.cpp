#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;k=min(k,n);const long long NEG=LLONG_MIN/4;
vector<vector<long long>>dp(n+2,vector<long long>(k+1,NEG));dp[0][0]=0;
for(int row=1;row<=n;++row){vector<vector<long long>>next(n+2,vector<long long>(k+1,NEG));
    for(int j=1;j<=row;++j){long long a;cin>>a;for(int c=0;c<=k;++c){long long old=max(dp[j-1][c],dp[j][c]);if(old!=NEG)next[j][c]=old+a;
        if(c){old=max(dp[j-1][c-1],dp[j][c-1]);if(old!=NEG)next[j][c]=max(next[j][c],old+3*a);}
    }}dp.swap(next);
}long long answer=NEG;for(int j=1;j<=n;++j)for(int c=0;c<=k;++c)answer=max(answer,dp[j][c]);cout<<answer<<'\n';
    return 0;
}
