#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
int total=n*(n+1)/2;
if(total%2){cout<<0<<'\n';return 0;}
int target=total/2;
vector<long long> dp(target+1); dp[0]=1;
for(int x=1;x<=n;++x){
    for(int sum=target;sum>=x;--sum) dp[sum]+=dp[sum-x];
}
// 每个无序划分由两个互补子集各计数一次。
cout<<dp[target]/2<<'\n';
    return 0;
}
