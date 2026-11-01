#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int N,P,C;cin>>N>>P>>C;vector<int>count(P+1);
for(int i=0,u;i<N;++i){cin>>u;++count[u];}
vector<vector<pair<int,int>>>g(P+1);for(int i=0;i<C;++i){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}
const long long INF=(1LL<<62);vector<long long>total(P+1);vector<int>reached(P+1);
using State=pair<long long,int>;
// 同住的牛共享一次最短路，再乘头数累加。
for(int s=1;s<=P;++s)if(count[s]){
    vector<long long>dist(P+1,INF);priority_queue<State,vector<State>,greater<State>>pq;// 堆条目保存这次入堆时的距离，旧条目稍后跳过。
dist[s]=0;pq.push({0,s});
    while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
        for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
    }
    for(int v=1;v<=P;++v)if(dist[v]!=INF){total[v]+=count[s]*dist[v];reached[v]+=count[s];}
}long long answer=INF;for(int v=1;v<=P;++v)if(reached[v]==N)answer=min(answer,total[v]);
cout<<(answer==INF?-1:answer)<<'\n';
    return 0;
}
