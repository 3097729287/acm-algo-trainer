#include <bits/stdc++.h>
using namespace std;
int main(){int n,m,s,t;cin>>n>>m>>s>>t;vector<pair<int,int>>es(m);vector<int>mn(n+1,n+1),d(n+1,999999);for(auto&[a,b]:es){cin>>a>>b;mn[a]=min(mn[a],b);}d[s]=0;
for(int k=0;k<n;k++)for(auto[a,b]:es)d[b]=min(d[b],d[a]+(b!=mn[a]));cout<<(d[t]==999999?-1:d[t])<<'\n';}
