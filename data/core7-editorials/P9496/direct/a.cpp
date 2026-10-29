#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){long long n,m;cin>>n>>m;
    if(n==m)cout<<0<<'\n';
    else if((n|m)==m||(n&m)==m)cout<<1<<'\n';
    else cout<<2<<'\n';
}
    return 0;
}
