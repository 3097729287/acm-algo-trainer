#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>topic(n+1),order(n),seen(n+1);for(int u=1;u<=n;++u)cin>>topic[u];iota(order.begin(),order.end(),1);
sort(order.begin(),order.end(),[&](int u,int v){return topic[u]!=topic[v]?topic[u]<topic[v]:u<v;});
for(int u:order){int count=0;for(int v:graph[u]){
    if(topic[v]==topic[u]){cout<<-1<<'\n';return 0;}
    if(topic[v]<topic[u]&&seen[topic[v]]!=u){seen[topic[v]]=u;++count;}
}if(count!=topic[u]-1){cout<<-1<<'\n';return 0;}}
for(int u:order)cout<<u<<' ';cout<<'\n';
    return 0;
}
