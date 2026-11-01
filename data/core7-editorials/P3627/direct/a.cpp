#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1),reverse_graph(n+1);vector<pair<int,int>>edges(m);
for(auto &e:edges){cin>>e.first>>e.second;graph[e.first].push_back(e.second);reverse_graph[e.second].push_back(e.first);}
vector<long long>money(n+1);for(int u=1;u<=n;++u)cin>>money[u];int start,p;cin>>start>>p;vector<int>bars(p);for(int &u:bars)cin>>u;
vector<int>seen(n+1),next_edge(n+1),order,stack;
for(int root=1;root<=n;++root)if(!seen[root]){seen[root]=1;stack.push_back(root);
    while(!stack.empty()){int u=stack.back();if(next_edge[u]<int(graph[u].size())){int v=graph[u][next_edge[u]++];if(!seen[v]){seen[v]=1;stack.push_back(v);}}
        else{order.push_back(u);stack.pop_back();}}
}
vector<int>component(n+1);int count=0;vector<long long>sum(1);
for(int at=n-1;at>=0;--at){int root=order[at];if(component[root])continue;++count;sum.push_back(0);component[root]=count;stack.push_back(root);
    while(!stack.empty()){int u=stack.back();stack.pop_back();sum[count]+=money[u];for(int v:reverse_graph[u])if(!component[v]){component[v]=count;stack.push_back(v);}}
}
vector<vector<int>>dag(count+1);vector<int>indegree(count+1);for(auto [u,v]:edges)if(component[u]!=component[v]){dag[component[u]].push_back(component[v]);++indegree[component[v]];}
vector<long long>best(count+1,-1);best[component[start]]=sum[component[start]];queue<int>ready;for(int u=1;u<=count;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:dag[u]){if(best[u]>=0)best[v]=max(best[v],best[u]+sum[v]);if(--indegree[v]==0)ready.push(v);}}
long long answer=0;for(int u:bars)answer=max(answer,best[component[u]]);cout<<answer<<'\n';
    return 0;
}
