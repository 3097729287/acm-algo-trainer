#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int throws,n;cin>>throws>>n;vector<int>score(n),required(n);
for(int i=0;i<n;++i){cin>>score[i];int item;while(cin>>item&&item) required[i]|=1<<(item-1);}
int states=1<<n;vector<double>dp(states),next(states);
for(int r=1;r<=throws;++r){
    for(int mask=0;mask<states;++mask){
        double sum=0;
        for(int j=0;j<n;++j){
            double best=dp[mask];
            if((mask&required[j])==required[j]) best=max(best,score[j]+dp[mask|(1<<j)]);
            sum+=best;
        }
        next[mask]=sum/n;
    }
    dp.swap(next);
}
cout<<fixed<<setprecision(6)<<dp[0]<<'\n';
    return 0;
}
