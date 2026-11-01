#include <bits/stdc++.h>
using namespace std;
struct DSU {
    vector<int>parent,size;
    DSU(int n):parent(n+1),size(n+1,1){iota(parent.begin(),parent.end(),0);}
    int find(int x){return parent[x]==x?x:parent[x]=find(parent[x]);}
    bool merge(int a,int b){
        a=find(a);b=find(b);if(a==b)return false;
        if(size[a]<size[b])swap(a,b);
        parent[b]=a;size[a]+=size[b];return true;
    }
};
struct Edge{long long square;int u,v;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){
    int satellites,n;cin>>satellites>>n;vector<pair<long long,long long>>point(n);
    for(auto &p:point)cin>>p.first>>p.second;vector<Edge>edges;
    for(int i=0;i<n;++i)for(int j=0;j<i;++j){long long dx=point[i].first-point[j].first,dy=point[i].second-point[j].second;edges.push_back({dx*dx+dy*dy,i,j});}
    sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.square<b.square;});
    DSU groups(n);int components=n;long long last=0;
    for(auto e:edges){if(components<=satellites)break;if(groups.merge(e.u,e.v)){--components;last=e.square;}}
    cout<<fixed<<setprecision(2)<<sqrt((double)last)<<'\n';
}
    return 0;
}
