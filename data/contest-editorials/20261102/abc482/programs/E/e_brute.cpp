#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;vector<vector<int>>d(n,vector<int>(n,n+1));for(int i=0;i<n;i++)d[i][i]=0;
for(int i=1,u,v;i<n;i++){cin>>u>>v;--u;--v;d[u][v]=d[v][u]=1;}vector<int>c(n);for(int &v:c)cin>>v;
for(int k=0;k<n;k++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)d[i][j]=min(d[i][j],d[i][k]+d[k][j]);
int diam=0;for(auto &row:d)for(int v:row)diam=max(diam,v);long long ans=0;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)ans+=c[i]==c[j]&&d[i][j]==diam;cout<<ans<<'\n';}
