#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<vector<pair<int,int>>>graph(n+1);
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back({v,i});graph[v].push_back({u,i});}
    vector<int>dfn(n+1),low(n+1),parent(n+1),parent_edge(n+1,-1),next_edge(n+1),bridge(m),stack{1};int timer=1;dfn[1]=low[1]=1;
    while(!stack.empty()){int u=stack.back();if(next_edge[u]<int(graph[u].size())){auto [v,id]=graph[u][next_edge[u]++];if(id==parent_edge[u])continue;
            if(!dfn[v]){parent[v]=u;parent_edge[v]=id;dfn[v]=low[v]=++timer;stack.push_back(v);}else low[u]=min(low[u],dfn[v]);
        }else{stack.pop_back();if(parent[u]){int p=parent[u];if(low[u]>dfn[p])bridge[parent_edge[u]]=1;low[p]=min(low[p],low[u]);}}}
    if(timer!=n){cout<<-1<<'\n';continue;}
    vector<int>black(n+1);black[1]=1;stack.push_back(1);int count=1;
    while(!stack.empty()){int u=stack.back();stack.pop_back();for(auto [v,id]:graph[u])if(bridge[id]&&!black[v]){black[v]=1;++count;stack.push_back(v);}}
    if(count==n){cout<<-1<<'\n';continue;}
    for(int u=1;u<=n;++u)cout<<(black[u]?'B':'W');cout<<'\n';
}
    return 0;
}
