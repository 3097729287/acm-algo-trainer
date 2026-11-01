#include <bits/stdc++.h>
using namespace std;
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<vector<int>>g(n),children(n);for(int i=1,u,v;i<n;i++){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),order={0};parent[0]=0;for(int at=0;at<n;at++){int u=order[at];for(int v:g[u])if(v!=parent[u]){parent[v]=u;children[u].push_back(v);order.push_back(v);}}
string x,y;cin>>x>>y;set<string>seen;int pulses=0,answer=-1;while(seen.insert(x).second){if(x==y){answer=pulses;break;}vector<int>q={0};for(int at=0;at<(int)q.size();at++){int u=q[at];if(x[u]=='0')x[u]='1';else{x[u]='0';for(int v:children[u])q.push_back(v);}}++pulses;}cout<<answer<<'\n';}}
