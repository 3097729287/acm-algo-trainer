#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,root;cin>>n>>root;--root;
struct Edge{int to;long long time;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={root};parent[root]=root;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(auto edge:g[u]) if(edge.to!=parent[u]){parent[edge.to]=u;order.push_back(edge.to);}}
vector<long long>height(n);long long answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];long long longest=0;
    for(auto edge:g[u]) if(parent[edge.to]==u) longest=max(longest,height[edge.to]+edge.time);
    for(auto edge:g[u]) if(parent[edge.to]==u) answer+=longest-height[edge.to]-edge.time;
    height[u]=longest;
}
cout<<answer<<'\n';
    return 0;
}
