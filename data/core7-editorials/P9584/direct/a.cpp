#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,queries;cin>>n>>queries;
struct Edge{int to;long long length;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={0},size(n,1);parent[0]=0;
vector<long long>depth(n),edgeToParent(n),value(n);
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];value[0]+=depth[u];
    for(auto edge:g[u]) if(edge.to!=parent[u]){int v=edge.to;parent[v]=u;depth[v]=depth[u]+edge.length;edgeToParent[v]=edge.length;order.push_back(v);}
}
const long long MOD=998244353;long long pairs=0;
for(int pos=n-1;pos>0;--pos){
    int u=order[pos];
    pairs=(pairs+edgeToParent[u]%MOD*size[u]%MOD*(n-size[u]))%MOD;
    size[parent[u]]+=size[u];
}
for(int u:order) for(auto edge:g[u]) if(parent[edge.to]==u){int v=edge.to;value[v]=value[u]+edge.length*(n-2*size[v]);}
while(queries--){
    int k;long long w;cin>>k>>w;--k;
    long long added=(value[k]%MOD+(n%MOD)*(w%MOD))%MOD;
    cout<<(2*pairs+2*added)%MOD<<'\n';
}
    return 0;
}
