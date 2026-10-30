#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n;long long initial;cin>>n>>initial;long long low=initial,high=initial,time=0;bool possible=true;
    for(int i=0;i<n;++i){long long t,l,h;cin>>t>>l>>h;long long elapsed=t-time;
        // 时间经过先扩张可达范围，再与预约求交。
        if(possible){low=max(low-elapsed,l);high=min(high+elapsed,h);if(low>high)possible=false;}time=t;
    }
    cout<<(possible?"YES":"NO")<<'\n';
}
    return 0;
}
