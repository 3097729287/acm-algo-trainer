#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;const long long mod=1000000007;
while(tests--){int n;cin>>n;vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
    vector<int>parent(n+1),order={1};for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    vector<long long>size(n+1,1),weight;for(int at=n-1;at>0;--at){int u=order[at];weight.push_back(size[u]*(n-size[u]));size[parent[u]]+=size[u];}
    sort(weight.begin(),weight.end());int m;cin>>m;vector<long long>factor(m);for(auto &p:factor)cin>>p;sort(factor.begin(),factor.end());int edges=n-1;
    if(m<edges){factor.resize(edges,1);sort(factor.begin(),factor.end());}
    else if(m>edges){long long combined=1;for(int i=edges-1;i<m;++i)combined=combined*factor[i]%mod;
        factor.resize(edges);factor.back()=combined; // 模值再小，也仍配给最大系数。
    }
    long long answer=0;for(int i=0;i<edges;++i)answer=(answer+(weight[i]%mod)*factor[i])%mod;
    cout<<answer<<'\n';
}
    return 0;
}
