#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n;long long k;cin>>n>>k;vector<long long>a(n);long long minimum=LLONG_MAX;
    for(auto &x:a){cin>>x;minimum=min(minimum,x);}long long lo=minimum,hi=minimum+k;
    while(lo<hi){long long mid=lo+(hi-lo+1)/2,cost=0;for(long long x:a){if(x<mid)cost+=mid-x;if(cost>k)break;}
        if(cost<=k)lo=mid;else hi=mid-1;
    }
    // 先抬满最低频数，余钱再给不同的最低频类型。
    long long used=0,extra=0;for(long long x:a){if(x<lo)used+=lo-x;else if(x>lo)++extra;}
    cout<<(lo-1)*n+1+extra+(k-used)<<'\n';
}
    return 0;
}
