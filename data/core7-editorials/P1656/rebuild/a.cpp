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
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<pair<int,int>>edge(m),answer;
for(auto &e:edge)cin>>e.first>>e.second;
for(int skip=0;skip<m;++skip){DSU groups(n);int components=n;
    for(int i=0;i<m;++i)if(i!=skip&&groups.merge(edge[i].first,edge[i].second))--components;
    if(components>1)answer.push_back(minmax(edge[skip].first,edge[skip].second));
}
sort(answer.begin(),answer.end());for(auto e:answer)cout<<e.first<<' '<<e.second<<'\n';
    return 0;
}
