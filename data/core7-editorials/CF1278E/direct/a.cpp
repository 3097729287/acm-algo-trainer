#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),left(n),right(n),stack{0};parent[0]=0;int timer=0;left[0]=++timer;
while(!stack.empty()){int u=stack.back();stack.pop_back();
    for(int v:g[u])if(v!=parent[u]){parent[v]=u;left[v]=++timer;}
    right[u]=++timer;
    for(int v:g[u])if(v!=parent[u])stack.push_back(v);
}for(int u=0;u<n;++u)cout<<left[u]<<' '<<right[u]<<'\n';
    return 0;
}
