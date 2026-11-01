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
int n,m;cin>>n>>m;map<string,int>id;for(int i=1;i<=n;++i){string name;cin>>name;id[name]=i;}
DSU groups(n);
for(int i=0;i<m;++i){string a,b;cin>>a>>b;groups.merge(id[a],id[b]);}
int queries;cin>>queries;
while(queries--){string a,b;cin>>a>>b;cout<<(groups.find(id[a])==groups.find(id[b])?"Yes.":"No.")<<'\n';}
    return 0;
}
