#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>k(n);for(auto &x:k)cin>>x;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}int s;cin>>s;--s;
vector<int>parent(n,-1),order{s};parent[s]=s;for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(parent[v]<0){parent[v]=u;order.push_back(v);}}
vector<long long>dp(n),used(n);for(int i=n-1;i>=0;--i){int u=order[i];vector<pair<long long,long long>>choice;
    for(int v:g[u])if(parent[v]==u&&v!=u)choice.push_back({1+dp[v],k[v]-1-used[v]});
    sort(choice.begin(),choice.end(),greater<pair<long long,long long>>());long long budget=k[u]-(u!=s),spare=0;
    for(const auto &[gain,remaining]:choice){if(used[u]==budget)break;dp[u]+=gain;spare+=remaining;++used[u];}
    long long extra=min(budget-used[u],spare);dp[u]+=extra;used[u]+=extra;
}cout<<2*dp[s]<<'\n';
    return 0;
}
