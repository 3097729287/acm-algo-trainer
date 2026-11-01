#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<array<int,3>>edges(m);vector<vector<int>>graph(n+1);vector<int>indegree(n+1),position(n+1);
    for(auto &e:edges){cin>>e[0]>>e[1]>>e[2];if(e[0]){graph[e[1]].push_back(e[2]);++indegree[e[2]];}}
    queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);int count=0;
    while(!ready.empty()){int u=ready.front();ready.pop();position[u]=++count;for(int v:graph[u])if(--indegree[v]==0)ready.push(v);}
    if(count!=n){cout<<"NO\n";continue;}cout<<"YES\n";
    for(auto e:edges){int u=e[1],v=e[2];if(!e[0]&&position[u]>position[v])swap(u,v);cout<<u<<' '<<v<<'\n';}
}
    return 0;
}
