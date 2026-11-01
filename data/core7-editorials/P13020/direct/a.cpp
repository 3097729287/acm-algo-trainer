#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>degree(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;++degree[u];++degree[v];}
if(n==1){cout<<1<<'\n';return 0;}
const long long MOD=1000000000;
vector<long long>factorial(n+1,1);
for(int i=1;i<=n;++i) factorial[i]=factorial[i-1]*i%MOD;
long long product=1;
for(int d:degree) product=product*factorial[d-1]%MOD;
cout<<product*(2LL*(n-1)%MOD)%MOD<<'\n';
    return 0;
}
