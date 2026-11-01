#include <bits/stdc++.h>
using namespace std;
struct Point{long long x,y;};struct Job{int u;vector<int>ids;};
__int128 cross(Point p,Point a,Point b){return (__int128)(a.x-p.x)*(b.y-p.y)-(__int128)(a.y-p.y)*(b.x-p.x);}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<Point>point(n);for(auto &p:point)cin>>p.x>>p.y;vector<int>parent(n,-1),order{0},size(n,1);parent[0]=0;
for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(parent[v]<0){parent[v]=u;order.push_back(v);}}
for(int i=n-1;i>0;--i)size[parent[order[i]]]+=size[order[i]];
vector<int>all(n),answer(n);iota(all.begin(),all.end(),0);vector<Job>jobs;jobs.push_back({0,all});
while(!jobs.empty()){Job job=jobs.back();jobs.pop_back();int u=job.u;auto &ids=job.ids;
    auto pivot=min_element(ids.begin(),ids.end(),[&](int a,int b){return tie(point[a].y,point[a].x)<tie(point[b].y,point[b].x);});
    iter_swap(ids.begin(),pivot);int p=ids[0];answer[p]=u+1;
    sort(ids.begin()+1,ids.end(),[&](int a,int b){return cross(point[p],point[a],point[b])>0;});
    int next=1;for(int v:g[u])if(parent[v]==u&&v!=u){vector<int>part(ids.begin()+next,ids.begin()+next+size[v]);next+=size[v];jobs.push_back({v,part});}
}for(int i=0;i<n;++i)cout<<answer[i]<<(i+1==n?'\n':' ');
    return 0;
}
