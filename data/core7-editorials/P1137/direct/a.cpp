#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1),best(n+1,1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:graph[u]){
    best[v]=max(best[v],best[u]+1);if(--indegree[v]==0)ready.push(v);
}}for(int u=1;u<=n;++u)cout<<best[u]<<'\n';
    return 0;
}
