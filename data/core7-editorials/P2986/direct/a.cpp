#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>cows(n);long long total=0;
for(auto &x:cows){cin>>x;total+=x;}
struct Edge{int to;long long length;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={0};parent[0]=0;
vector<long long>distance(n),mass=cows,value(n);
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];value[0]+=cows[u]*distance[u];
    for(auto edge:g[u]) if(edge.to!=parent[u]){parent[edge.to]=u;distance[edge.to]=distance[u]+edge.length;order.push_back(edge.to);}
}
for(int pos=n-1;pos>0;--pos){int u=order[pos];mass[parent[u]]+=mass[u];}
long long answer=value[0];
for(int u:order){
    for(auto edge:g[u]) if(parent[edge.to]==u){
        int v=edge.to;value[v]=value[u]+edge.length*(total-2*mass[v]);answer=min(answer,value[v]);
    }
}
cout<<answer<<'\n';
    return 0;
}
