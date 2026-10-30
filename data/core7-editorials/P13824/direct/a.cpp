#include <bits/stdc++.h>
using namespace std;
struct Point{long long x,y;};
long long distance2(const Point&a,const Point&b){long long x=a.x-b.x,y=a.y-b.y;return x*x+y*y;}
struct Option{long long required,length;int u,v;};
bool by_requirement(const Option&a,const Option&b){return a.required<b.required;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,queries;cin>>n>>queries;vector<Point>point(n+1);for(int i=1;i<=n;++i)cin>>point[i].x>>point[i].y;
vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>parent(n+1),order={1};vector<long long>edge_length(n+1);
for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;edge_length[v]=distance2(point[u],point[v]);order.push_back(v);}}
vector<vector<int>>ancestor(n+1,vector<int>(n+1));
for(int v=1;v<=n;++v)for(int u=v;u!=0;u=parent[u])ancestor[u][v]=1;
vector<vector<long long>>required(n+1,vector<long long>(n+1)),length(n+1,vector<long long>(n+1));
for(int u:order)for(int v:order)if(u!=v){
    bool move_u=!ancestor[u][v],move_v=!ancestor[v][u];long long next=LLONG_MAX;
    if(move_u)next=min(next,required[parent[u]][v]);if(move_v)next=min(next,required[u][parent[v]]);
    if(move_u&&move_v)next=min(next,required[parent[u]][parent[v]]); // 两人同时移动不能漏
    required[u][v]=max(distance2(point[u],point[v]),next);
    if(move_u)length[u][v]=edge_length[u]+length[parent[u]][v];
    else length[u][v]=edge_length[v]+length[u][parent[v]];
}
vector<Option>options;options.reserve(n*(n+1)/2);
for(int u=1;u<=n;++u)for(int v=u;v<=n;++v)options.push_back({required[u][v],length[u][v],u,v});
sort(options.begin(),options.end(),by_requirement);vector<long long>threshold;vector<int>best_u,best_v;
threshold.reserve(options.size());best_u.reserve(options.size());best_v.reserve(options.size());long long best_length=-1;int p=1,q=1;
for(auto option:options){
    if(option.length>best_length||(option.length==best_length&&(option.u<p||(option.u==p&&option.v<q)))){best_length=option.length;p=option.u;q=option.v;}
    threshold.push_back(option.required);best_u.push_back(p);best_v.push_back(q);
}
while(queries--){long long d;cin>>d;int at=(int)(upper_bound(threshold.begin(),threshold.end(),d)-threshold.begin())-1;cout<<best_u[at]<<' '<<best_v[at]<<'\n';}
    return 0;
}
