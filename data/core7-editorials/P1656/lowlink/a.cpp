#include <bits/stdc++.h>
using namespace std;
int vertices,timer=0;vector<vector<pair<int,int>>>graph;vector<int>dfn,low;vector<pair<int,int>>bridges;
void dfs(int u,int parent_edge){
    dfn[u]=low[u]=++timer;
    for(auto [v,id]:graph[u]){
        if(id==parent_edge)continue;
        if(!dfn[v]){dfs(v,id);low[u]=min(low[u],low[v]);if(low[v]>dfn[u])bridges.push_back(minmax(u,v));}
        else low[u]=min(low[u],dfn[v]);
    }
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m;cin>>vertices>>m;graph.assign(vertices+1,{});dfn.assign(vertices+1,0);low.assign(vertices+1,0);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back({v,i});graph[v].push_back({u,i});}
for(int u=1;u<=vertices;++u)if(!dfn[u])dfs(u,-1);
sort(bridges.begin(),bridges.end());for(auto e:bridges)cout<<e.first<<' '<<e.second<<'\n';
    return 0;
}
