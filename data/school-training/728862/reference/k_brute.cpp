#include <bits/stdc++.h>
using namespace std;
struct Edge{int t,u,v;};
int main(){int t;cin>>t;while(t--){int n,m;cin>>n>>m;vector<Edge>e(m);for(auto&a:e){cin>>a.t>>a.u>>a.v;--a.u;--a.v;}vector<int>p(n),pos(n);iota(p.begin(),p.end(),0);bool ok=false;do{for(int i=0;i<n;++i)pos[p[i]]=i;ok=true;for(auto a:e)if(a.t&&pos[a.u]>pos[a.v])ok=false;if(ok)break;}while(next_permutation(p.begin(),p.end()));if(!ok){cout<<"NO\n";continue;}cout<<"YES\n";for(auto a:e){if(!a.t&&pos[a.u]>pos[a.v])swap(a.u,a.v);cout<<a.u+1<<' '<<a.v+1<<'\n';}}}
