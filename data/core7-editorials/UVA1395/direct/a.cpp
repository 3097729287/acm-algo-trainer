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
int n,m;while(cin>>n>>m&&(n||m)){vector<Edge>edges(m);for(auto &e:edges)cin>>e.u>>e.v>>e.weight;
    sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.weight<b.weight;});int answer=INT_MAX;
    for(int left=0;left<m;++left){DSU groups(n);int chosen=0;
        for(int right=left;right<m;++right)if(groups.merge(edges[right].u,edges[right].v)){
            if(++chosen==n-1){answer=min(answer,edges[right].weight-edges[left].weight);break;}
        }
        if(chosen<n-1)break;
    }
    cout<<(answer==INT_MAX?-1:answer)<<'\n';
}
    return 0;
}
