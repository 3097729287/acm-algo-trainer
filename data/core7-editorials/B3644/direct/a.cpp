#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);
for(int u=1;u<=n;++u){int v;while(cin>>v&&v){graph[u].push_back(v);++indegree[v];}}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();cout<<u<<' ';
    for(int v:graph[u])if(--indegree[v]==0)ready.push(v);
}cout<<'\n';
    return 0;
}
