#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;while(cin>>n>>m){vector<int>parent(n+m+1),rankSize(n+m+1,1),count(n+m+1),pos(n+1);vector<long long>sum(n+m+1);
    iota(parent.begin(),parent.end(),0);for(int i=1;i<=n;++i){pos[i]=i;count[i]=1;sum[i]=i;}int nodes=n;
    auto root=[&](int u){while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;};
    while(m--){int type,p,q;cin>>type>>p;int a=root(pos[p]);
        if(type==3){cout<<count[a]<<' '<<sum[a]<<'\n';continue;}cin>>q;int b=root(pos[q]);if(a==b)continue;
        if(type==1){if(rankSize[a]<rankSize[b])swap(a,b);parent[b]=a;rankSize[a]+=rankSize[b];count[a]+=count[b];sum[a]+=sum[b];}
        else{--count[a];sum[a]-=p;int id=++nodes;pos[p]=id;parent[id]=b;++rankSize[b];++count[b];sum[b]+=p;}
    }
}
    return 0;
}
