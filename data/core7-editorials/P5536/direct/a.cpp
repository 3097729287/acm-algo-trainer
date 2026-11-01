#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n),distance(n),order;
auto farthest=[&](int s){fill(distance.begin(),distance.end(),-1);order={s};distance[s]=0;parent[s]=s;
    for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(distance[v]<0){distance[v]=distance[u]+1;parent[v]=u;order.push_back(v);}}
    return int(max_element(distance.begin(),distance.end())-distance.begin());
};int a=farthest(0),b=farthest(a);vector<int>path;for(int u=b;;u=parent[u]){path.push_back(u);if(u==a)break;}
int center=path[path.size()/2];farthest(center);vector<int>height(n);
for(int i=n-1;i>0;--i){int u=order[i];height[parent[u]]=max(height[parent[u]],height[u]+1);}
sort(height.begin(),height.end(),greater<int>());cout<<height[k]+1<<'\n';
    return 0;
}
