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
int a,b,p;cin>>a>>b>>p;vector<int>composite(b+1);DSU groups(b);int components=b-a+1;
for(int q=2;q<=b;++q)if(!composite[q]){
    if(q<=b/q)for(int multiple=q*q;multiple<=b;multiple+=q)composite[multiple]=1;
    if(q<p)continue;int first=(a+q-1)/q*q;
    for(int x=first+q;x<=b;x+=q)if(groups.merge(first,x))--components;
}
cout<<components<<'\n';
    return 0;
}
