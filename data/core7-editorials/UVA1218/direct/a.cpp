#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;
while(cin>>n&&n!=-1){
    if(n==0) continue;
    vector<vector<int>>g(n);
    for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
    vector<int>parent(n,-1),order={0};parent[0]=0;
    for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    const long long INF=1000000000000000LL;
    vector<long long>server(n),byParent(n),byChild(n);
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos];server[u]=1;long long zero=0,one=INF;
        for(int v:g[u]) if(parent[v]==u){
            server[u]+=min(server[v],byParent[v]);
            one=min(min(INF,one+byChild[v]),min(INF,zero+server[v]));
            zero=min(INF,zero+byChild[v]);
        }
        byParent[u]=zero;byChild[u]=one;
    }
    cout<<min(server[0],byChild[0])<<'\n';
}
    return 0;
}
