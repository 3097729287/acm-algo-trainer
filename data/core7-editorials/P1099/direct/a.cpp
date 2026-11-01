#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long limit;cin>>n>>limit;vector<vector<pair<int,int>>>g(n);
for(int i=1,u,v,w;i<n;++i){cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<vector<long long>>d(n,vector<long long>(n));vector<vector<int>>parent(n,vector<int>(n,-1));
for(int s=0;s<n;++s){vector<int>order{s};parent[s][s]=s;
    for(size_t j=0;j<order.size();++j){int u=order[j];for(auto [v,w]:g[u])if(parent[s][v]<0){parent[s][v]=u;d[s][v]=d[s][u]+w;order.push_back(v);}}
}
int a=max_element(d[0].begin(),d[0].end())-d[0].begin(),b=max_element(d[a].begin(),d[a].end())-d[a].begin();
vector<int>path;for(int u=b;;u=parent[a][u]){path.push_back(u);if(u==a)break;}
long long answer=LLONG_MAX;for(int a:path)for(int b:path)if(d[a][b]<=limit){long long worst=0;
    for(int v=0;v<n;++v)worst=max(worst,(d[v][a]+d[v][b]-d[a][b])/2);answer=min(answer,worst);
}cout<<answer<<'\n';
    return 0;
}
