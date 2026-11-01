#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1),order;
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);bool multiple=false;
while(!ready.empty()){if(ready.size()>1)multiple=true;int u=ready.front();ready.pop();order.push_back(u);
    for(int v:graph[u])if(--indegree[v]==0)ready.push(v);
}for(int u:order)cout<<u<<'\n';cout<<multiple<<'\n';
    return 0;
}
