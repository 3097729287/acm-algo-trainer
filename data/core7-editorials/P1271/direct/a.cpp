#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>count(n+1);
for(int i=0;i<m;++i){int x;cin>>x;++count[x];}
bool first=true;for(int x=1;x<=n;++x)for(int k=0;k<count[x];++k){if(!first)cout<<' ';cout<<x;first=false;}cout<<'\n';
    return 0;
}
