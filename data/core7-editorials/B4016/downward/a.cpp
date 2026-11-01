#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n; vector<vector<int>> g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int> parent(n,-1),order={0}; parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];
    for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}
}
vector<int> down(n); int answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos],first=0,second=0;
    for(int v:g[u]) if(parent[v]==u){
        int length=down[v]+1;
        if(length>first){second=first;first=length;}
        else second=max(second,length);
    }
    down[u]=first; answer=max(answer,first+second);
}
cout<<answer<<'\n';
    return 0;
}
