#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;cin>>n>>m;vector<string>s(n);for(auto &x:s)cin>>x;
set<pair<int,int>> border;for(int i=0;i<n;i++){border.insert({i,0});border.insert({i,m-1});}
for(int j=0;j<m;j++){border.insert({0,j});border.insert({n-1,j});}
int ans=0;for(auto p:border)ans+=s[p.first][p.second]=='#';cout<<ans<<'\n';}
