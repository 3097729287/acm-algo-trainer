#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,limit;cin>>n>>m>>limit;vector<char>marked(n);
for(int i=0,u;i<m;++i){cin>>u;marked[u-1]=true;}
vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
const int NEG=-1000000000;vector<int>down(n,NEG),up(n,NEG);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];if(marked[u]) down[u]=0;
    for(int v:g[u]) if(parent[v]==u&&down[v]>=0) down[u]=max(down[u],down[v]+1);
}
for(int u:order){
    int first=max(up[u],marked[u]?0:NEG),second=NEG,owner=-1;
    for(int v:g[u]) if(parent[v]==u&&down[v]>=0){
        int value=down[v]+1;
        if(value>first){second=first;first=value;owner=v;}
        else second=max(second,value);
    }
    for(int v:g[u]) if(parent[v]==u){int best=owner==v?second:first;if(best>=0) up[v]=best+1;}
}
int answer=0;
for(int u=0;u<n;++u) if(max(down[u],up[u])<=limit) ++answer;
cout<<answer<<'\n';
    return 0;
}
