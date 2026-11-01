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
int n;cin>>n;DSU groups(25);vector<int>used(26),seen(26);int answer=0;
for(int i=0;i<n;++i){string s;cin>>s;int first=s[0]-'a';for(char c:s){int x=c-'a';used[x]=1;groups.merge(first,x);}}
for(int x=0;x<26;++x)if(used[x]){int root=groups.find(x);if(!seen[root]){seen[root]=1;++answer;}}
cout<<answer<<'\n';
    return 0;
}
