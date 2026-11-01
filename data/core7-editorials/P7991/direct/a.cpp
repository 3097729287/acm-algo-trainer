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
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;DSU groups(n);
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;groups.merge(u,v);}vector<int>root(n+1);for(int i=1;i<=n;++i)root[i]=groups.find(i);
    int start=root[1],finish=root[n];if(start==finish){cout<<0<<'\n';continue;}
    const long long infinity=1LL<<60;vector<long long>a(n+1,infinity),b(n+1,infinity);
    for(int direction:{1,-1}){int nearestA=-1,nearestB=-1;
        for(int i=direction==1?1:n;1<=i&&i<=n;i+=direction){
            if(root[i]==start)nearestA=i;if(root[i]==finish)nearestB=i;
            if(nearestA!=-1){long long delta=i-nearestA;a[root[i]]=min(a[root[i]],delta*delta);}
            if(nearestB!=-1){long long delta=i-nearestB;b[root[i]]=min(b[root[i]],delta*delta);}
        }
    }
    long long answer=infinity;for(int i=1;i<=n;++i)if(root[i]==i)answer=min(answer,a[i]+b[i]);cout<<answer<<'\n';
}
    return 0;
}
