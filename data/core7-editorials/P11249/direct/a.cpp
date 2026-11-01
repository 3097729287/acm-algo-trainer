#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests; cin>>tests;
while(tests--){
    int n;cin>>n;vector<int> treasure(n),degree(n);for(int &x:treasure) cin>>x;
    vector<vector<int>>g(n);
    for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);++degree[u];++degree[v];}
    vector<char> alive(n,true); queue<int>q;
    for(int u=0;u<n;++u) if(!treasure[u]&&degree[u]<=1) q.push(u);
    while(!q.empty()){
        int u=q.front();q.pop();if(!alive[u]) continue;alive[u]=false;
        for(int v:g[u]) if(alive[v]){
            --degree[v];if(!treasure[v]&&degree[v]<=1) q.push(v);
        }
    }
    bool possible=true;
    for(int u=0;u<n;++u) if(alive[u]&&degree[u]>2) possible=false;
    cout<<(possible?"Yes":"No")<<'\n';
}
    return 0;
}
