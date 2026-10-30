#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int queries;cin>>queries;while(queries--){long long k;cin>>k;long long lo=0,hi=2000000000LL;
    while(lo<hi){long long mid=(lo+hi)/2;if((mid+1)*(2*mid+1)>=k)hi=mid;else lo=mid+1;}
    // 找到波段后，转换为从零开始的段内偏移。
    long long i=lo,t=k-i*(2*i-1)-1;
    if(t<=i)cout<<t<<'\n';else if(t<=3*i)cout<<2*i-t<<'\n';else cout<<t-4*i<<'\n';
}
    return 0;
}
