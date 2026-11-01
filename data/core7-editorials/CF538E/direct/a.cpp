#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>child(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;child[u-1].push_back(v-1);}
vector<int>depth(n),order{0};for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:child[u]){depth[v]=depth[u]+1;order.push_back(v);}}
vector<int>high(n),low(n);int leaves=0;for(int i=n-1;i>=0;--i){int u=order[i];if(child[u].empty()){high[u]=low[u]=1;++leaves;continue;}
    int sumHigh=0,sumLow=0,minHigh=n,minLow=n;for(int v:child[u]){sumHigh+=high[v];sumLow+=low[v];minHigh=min(minHigh,high[v]);minLow=min(minLow,low[v]);}
    if(depth[u]%2==0){high[u]=minHigh;low[u]=sumLow;}else{high[u]=sumHigh;low[u]=minLow;}
}cout<<leaves-high[0]+1<<' '<<low[0]<<'\n';
    return 0;
}
