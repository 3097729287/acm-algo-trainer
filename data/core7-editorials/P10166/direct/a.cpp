#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>weight(n+1),ancestor(n+1,LLONG_MAX/4);
long long first=LLONG_MAX/4,second=LLONG_MAX/4;
for(int u=1;u<=n;++u){cin>>weight[u];if(weight[u]<first){second=first;first=weight[u];}else second=min(second,weight[u]);}
vector<vector<int>>graph(n+1);vector<int>indegree(n+1);for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);int removed=0;long long answer=2*(first+second);
while(!ready.empty()){int u=ready.front();ready.pop();++removed;answer=min(answer,weight[u]+ancestor[u]);
    for(int v:graph[u]){ancestor[v]=min(ancestor[v],min(ancestor[u],weight[u]));if(--indegree[v]==0)ready.push(v);}
}cout<<(removed<n?0:answer)<<'\n';
    return 0;
}
