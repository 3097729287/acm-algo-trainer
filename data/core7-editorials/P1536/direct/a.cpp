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
int n;
while(cin>>n&&n){
    int m;cin>>m;DSU groups(n);int components=n;
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;if(groups.merge(u,v))--components;}
    cout<<components-1<<'\n';
}
    return 0;
}
