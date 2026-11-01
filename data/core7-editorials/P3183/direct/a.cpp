#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);vector<long long>ways(n+1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}vector<int>original=indegree;
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u]){ready.push(u);ways[u]=1;}
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:graph[u]){ways[v]+=ways[u];if(--indegree[v]==0)ready.push(v);}}
long long answer=0;for(int u=1;u<=n;++u)if(graph[u].empty()&&original[u])answer+=ways[u];cout<<answer<<'\n';
    return 0;
}
