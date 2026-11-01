#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>color(n+1,-1);int minimum=0,maximum=0;
for(int start=1;start<=n;++start)if(color[start]==-1){
    int count[2]={1,0};queue<int>todo;todo.push(start);color[start]=0;
    while(!todo.empty()){int u=todo.front();todo.pop();for(int v:graph[u])if(color[v]==-1){color[v]=color[u]^1;++count[color[v]];todo.push(v);}}
    minimum+=min(count[0],count[1]);maximum+=max(count[0],count[1]);
}
cout<<minimum<<' '<<maximum<<'\n';
    return 0;
}
