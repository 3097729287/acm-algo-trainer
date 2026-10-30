#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const long long MOD=998244353;int n;cin>>n;long long count[41]={},sum[41]={},weighted[41]={};
long long ways=1,total=0;
for(int i=0;i<n;++i){int x;cin>>x;
    count[x]=(count[x]+ways)%MOD;sum[x]=(sum[x]+total)%MOD;weighted[x]=(weighted[x]+ways)%MOD;
    for(int v=1;v<=40;++v)weighted[v]=weighted[v]*x%MOD;
    ways=count[x];total=(sum[x]+weighted[x])%MOD;
}
cout<<total<<'\n';
    return 0;
}
