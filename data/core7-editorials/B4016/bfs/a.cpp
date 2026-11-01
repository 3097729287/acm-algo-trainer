#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n; vector<vector<int>> g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
auto distances=[&](int start){
    vector<int> d(n,-1); queue<int> q; q.push(start); d[start]=0;
    while(!q.empty()){
        int u=q.front();q.pop();
        for(int v:g[u]) if(d[v]<0){d[v]=d[u]+1;q.push(v);}
    }
    return d;
};
auto d=distances(0);int endpoint=0;
for(int u=1;u<n;++u) if(d[u]>d[endpoint]) endpoint=u;
// 从一个最远端点再搜索，才得到全树直径。
d=distances(endpoint);
int diameter=0;for(int length:d) diameter=max(diameter,length);
cout<<diameter<<'\n';
    return 0;
}
