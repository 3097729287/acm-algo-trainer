#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){
    int n,m;cin>>n>>m;vector<long long>a(n+1);for(int i=1;i<=n;++i)cin>>a[i];vector<int>difference(n+2);
    while(m--){int l,r;cin>>l>>r;++difference[l];--difference[r+1];}
    int count=0;long long lower=LLONG_MIN,upper=LLONG_MAX;
    for(int i=1;i<=n;++i){count+=difference[i];lower=max(lower,a[i]-count);upper=min(upper,a[i]+count);}
    cout<<max(0LL,lower-upper)<<'\n';
}
    return 0;
}
