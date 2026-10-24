#include <bits/stdc++.h>
using namespace std;
bool better(const string&a,const string&b){return b.empty()||a.size()<b.size()||(a.size()==b.size()&&a<b);}
int main(){int n,m;cin>>n>>m;vector<tuple<int,int,char>>e;while(m--){int a,b,c;cin>>a>>b>>c;e.push_back({a,b,char('0'+c)});}vector<string>d(n+1);vector<bool>ok(n+1);ok[1]=true;
for(int k=0;k<n;k++){auto nd=d;auto no=ok;for(auto[a,b,c]:e)if(ok[a]&&b!=1){string s=d[a]+c;if(!no[b]||better(s,nd[b]))nd[b]=s,no[b]=true;}d=nd;ok=no;}
for(int i=2;i<=n;i++){long long x=0;for(char c:d[i])x=(x*10+c-'0')%998244353;cout<<x<<'\n';}}
