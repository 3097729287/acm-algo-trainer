#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<int>count(n+1);for(int i=0;i<2*k;++i){int u;cin>>u;count[u]=1;}
vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>parent(n+1),order={1};for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
long long answer=0;
for(int at=n-1;at>0;--at){int u=order[at];
    // 每条父边的贡献是两侧大学数的较小者。
    answer+=min(count[u],2*k-count[u]);count[parent[u]]+=count[u];
}
cout<<answer<<'\n';
    return 0;
}
