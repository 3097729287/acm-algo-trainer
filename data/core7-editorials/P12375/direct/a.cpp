#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int T;cin>>T;const long long MOD=998244353;
while(T--){long long n,m;cin>>n>>m;long long D=m-n;
    long long p=min(n-1,(long long)((3+sqrtl(9.0L+8.0L*D))/2));
    // 开根只是估计，最终边界用128位整数严格校正。
    while(p>0&&(__int128)p*(p-3)>(__int128)2*D)--p;
    while(p<n-1&&(__int128)(p+1)*(p-2)<=(__int128)2*D)++p;
    long long t=n-1-p;
    __int128 first=(__int128)p*(p-1)*(p+1)/6+p;
    __int128 second=(__int128)t*(2*D+p+n+2)/2;
    cout<<(long long)((first+second)%MOD)<<'\n';
}
    return 0;
}
