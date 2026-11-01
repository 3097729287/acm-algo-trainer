#include <bits/stdc++.h>
using namespace std;
using ll=long long;
struct Edge{ll w;int u,v;bool operator<(const Edge&o)const{return w<o.w;}};
int main(){int n;cin>>n;vector<ll>x(n),y(n),c(n),k(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];for(ll&v:c)cin>>v;for(ll&v:k)cin>>v;vector<Edge>e;for(int i=0;i<n;++i){e.push_back({c[i],n,i});for(int j=0;j<i;++j)e.push_back({(abs(x[i]-x[j])+abs(y[i]-y[j]))*(k[i]+k[j]),i,j});}sort(e.begin(),e.end());vector<int>part(n+1);iota(part.begin(),part.end(),0);ll ans=0;for(auto a:e)if(part[a.u]!=part[a.v]){int old=part[a.u],to=part[a.v];for(int&i:part)if(i==old)i=to;ans+=a.w;}cout<<ans<<'\n';}
