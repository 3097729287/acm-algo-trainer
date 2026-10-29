#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){int n;cin>>n;int zeros=0;
    for(int i=0;i<n;++i){int x;cin>>x;zeros+=x==0;}
    bool alice=n==1?zeros==1:n==2?zeros==0:zeros<n;
    cout<<(alice?"Alice":"Bob")<<'\n';
}
    return 0;
}
