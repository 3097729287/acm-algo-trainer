#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>to(n+1),indegree(n+1);vector<long long>value(n+1);long long answer=0;
for(int u=1;u<=n;++u){cin>>to[u]>>value[u];++indegree[to[u]];answer+=value[u];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();if(--indegree[to[u]]==0)ready.push(to[u]);}
for(int root=1;root<=n;++root)if(indegree[root]){long long least=LLONG_MAX;int u=root;while(indegree[u]){least=min(least,value[u]);indegree[u]=0;u=to[u];}answer-=least;}
cout<<answer<<'\n';
    return 0;
}
