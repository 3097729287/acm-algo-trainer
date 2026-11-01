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
struct Edge{int u,v,weight;};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges)cin>>e.u>>e.v>>e.weight;
    int forbidden=0,answer=0;
    for(int bit=29;bit>=0;--bit){int trial=forbidden|(1<<bit);DSU groups(n);int components=n;
        for(auto e:edges)if((e.weight&trial)==0&&groups.merge(e.u,e.v))--components;
        if(components==1)forbidden=trial;else answer|=1<<bit;
    }
    cout<<answer<<'\n';
}
    return 0;
}
