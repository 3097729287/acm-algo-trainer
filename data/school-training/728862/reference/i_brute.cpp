#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;vector<int>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];vector<vector<int>>r(n,vector<int>(n));for(int i=0;i<n;++i)for(int j=0;j<n;++j)r[i][j]=(x[i]==x[j]||y[i]==y[j]);for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)r[i][j]|=r[i][k]&&r[k][j];int count=0;for(int i=0;i<n;++i){bool first=true;for(int j=0;j<i;++j)if(r[i][j])first=false;count+=first;}cout<<count-1<<'\n';}
