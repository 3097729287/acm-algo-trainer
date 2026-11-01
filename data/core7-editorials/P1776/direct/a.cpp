#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,capacity; cin>>n>>capacity;
vector<long long> dp(capacity+1);
for(int i=0,value,weight,count;i<n;++i){
    cin>>value>>weight>>count;
    count=min(count,capacity/weight); // 装不下的多余件数无需拆分。
    for(int batch=1;count;batch*=2){
        int copies=min(batch,count); count-=copies;
        int w=weight*copies;
        long long v=1LL*value*copies;
        for(int c=capacity;c>=w;--c) dp[c]=max(dp[c],dp[c-w]+v);
    }
}
cout<<dp[capacity]<<'\n';
    return 0;
}
