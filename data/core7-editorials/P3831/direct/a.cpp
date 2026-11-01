#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;struct Point{int x,y;};int K=m+2;vector<Point>p(K);
for(int i=0;i<m;++i)cin>>p[i].x>>p[i].y;cin>>p[m].x>>p[m].y>>p[m+1].x>>p[m+1].y;
vector<vector<pair<int,int>>>g(2*K);auto edge=[&](int u,int v,int w){g[u].push_back({v,w});g[v].push_back({u,w});};
// 两层之间只有指定换乘站的一分钟边。
for(int i=0;i<m;++i)edge(2*i,2*i+1,1);
vector<int>order(K);iota(order.begin(),order.end(),0);
sort(order.begin(),order.end(),[&](int a,int b){return tie(p[a].x,p[a].y)<tie(p[b].x,p[b].y);});
for(int i=1;i<K;++i){int u=order[i-1],v=order[i];if(p[u].x==p[v].x)edge(2*u,2*v,2*(p[v].y-p[u].y));}
sort(order.begin(),order.end(),[&](int a,int b){return tie(p[a].y,p[a].x)<tie(p[b].y,p[b].x);});
for(int i=1;i<K;++i){int u=order[i-1],v=order[i];if(p[u].y==p[v].y)edge(2*u+1,2*v+1,2*(p[v].x-p[u].x));}
const long long INF=(1LL<<60);vector<long long>dist(2*K,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[2*m]=dist[2*m+1]=0;pq.push({0,2*m});pq.push({0,2*m+1});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}long long answer=min(dist[2*(m+1)],dist[2*(m+1)+1]);cout<<(answer==INF?-1:answer)<<'\n';
    return 0;
}
