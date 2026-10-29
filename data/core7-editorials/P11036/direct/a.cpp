#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){long long a;cin>>a;long long p=a&(-a);cout<<a<<' '<<2*p<<' '<<a+2*p<<'\n';}
    return 0;
}
