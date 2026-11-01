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
int n,q;cin>>n>>q;DSU groups(n);vector<int>used(n);int components=0,isolated=0;
unsigned long long full=(1ULL<<n)-1;
while(q--){unsigned long long value;cin>>value;if(value==full){++isolated;cout<<components+isolated<<'\n';continue;}
    int first=-1;
    for(int bit=0;bit<n;++bit)if(((value>>bit)&1ULL)==0){
        if(!used[bit]){used[bit]=1;++components;}
        if(first==-1)first=bit;else if(groups.merge(first,bit))--components;
    }
    cout<<components+isolated<<'\n';
}
    return 0;
}
