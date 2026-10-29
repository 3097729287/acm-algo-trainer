#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>a(n+1);for(int i=1;i<=n;++i)cin>>a[i];
while(m--){int k;cin>>k;cout<<a[k]<<'\n';}
    return 0;
}
