#include <bits/stdc++.h>
using namespace std;
using ll=long long;
int main(){int t;cin>>t;while(t--){ll a,b,x,y,n;cin>>a>>b>>x>>y>>n;ll ans=a*b;for(ll da=0;da<=min(n,a-x);++da)for(ll db=0;db<=min(n-da,b-y);++db)ans=min(ans,(a-da)*(b-db));cout<<ans<<'\n';}}
