#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,s,t;cin>>n>>s>>t;--s;--t;vector<int>l(n),r(n),h(n);for(int i=0;i<n;++i)cin>>l[i]>>r[i]>>h[i];
int finish=2*n;vector<vector<pair<int,int>>>g(finish+1);
for(int i=0;i<n;++i){g[2*i].push_back({2*i+1,r[i]-l[i]});g[2*i+1].push_back({2*i,r[i]-l[i]});}
// 目标挡板的任意落点都可以结束，无需再走到端点。
g[2*t].push_back({finish,0});g[2*t+1].push_back({finish,0});
for(int i=0;i<n;++i)for(int side=0;side<2;++side){int x=side?r[i]:l[i],level=-1;
    for(int j=0;j<n;++j)if(j!=i&&l[j]<=x&&x<=r[j]&&h[j]<=h[i])level=max(level,h[j]);
    if(level==-1)continue;
    for(int j=0;j<n;++j)if(j!=i&&h[j]==level&&l[j]<=x&&x<=r[j]){
        int fall=h[i]-h[j];g[2*i+side].push_back({2*j,fall+x-l[j]});g[2*i+side].push_back({2*j+1,fall+r[j]-x});
        if(j==t)g[2*i+side].push_back({finish,fall});
    }
}
const long long INF=(1LL<<60);vector<long long>dist(finish+1,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[2*s]=0;pq.push({0,2*s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}cout<<(dist[finish]==INF?-1:dist[finish])<<'\n';
    return 0;
}
