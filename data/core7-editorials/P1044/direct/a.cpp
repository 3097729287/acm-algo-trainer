#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>f(n+1);f[0]=1;
for(int size=1;size<=n;++size)
    for(int before=0;before<size;++before)
        f[size]+=f[before]*f[size-1-before];
cout<<f[n]<<'\n';
    return 0;
}
