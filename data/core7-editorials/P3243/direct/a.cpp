#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<vector<int>>previous(n+1);vector<int>outdegree(n+1),reversed;
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;previous[v].push_back(u);++outdegree[u];}
    priority_queue<int>ready;for(int u=1;u<=n;++u)if(!outdegree[u])ready.push(u);
    while(!ready.empty()){int u=ready.top();ready.pop();reversed.push_back(u);for(int v:previous[u])if(--outdegree[v]==0)ready.push(v);}
    if(int(reversed.size())!=n){cout<<"Impossible!\n";continue;}
    reverse(reversed.begin(),reversed.end());for(int u:reversed)cout<<u<<' ';cout<<'\n';
}
    return 0;
}
