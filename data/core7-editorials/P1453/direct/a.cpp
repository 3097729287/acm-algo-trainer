#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>weight(n);for(auto &x:weight) cin>>x;
vector<int>representative(n),componentSize(n,1);iota(representative.begin(),representative.end(),0);
auto find=[&](int x){while(representative[x]!=x){representative[x]=representative[representative[x]];x=representative[x];}return x;};
vector<vector<int>>g(n);int cycleU=-1,cycleV=-1;
for(int i=0,u,v;i<n;++i){
    cin>>u>>v;int a=find(u),b=find(v);
    if(a==b){cycleU=u;cycleV=v;}
    else{if(componentSize[a]<componentSize[b]) swap(a,b);representative[b]=a;componentSize[a]+=componentSize[b];g[u].push_back(v);g[v].push_back(u);}
}
double multiplier;cin>>multiplier;
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
auto solve=[&](int forbidden){
    vector<long long>take(n),skip(n);const long long NEG=LLONG_MIN/4;
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos];take[u]=weight[u];
        for(int v:g[u]) if(parent[v]==u){take[u]+=skip[v];skip[u]+=max(take[v],skip[v]);}
        if(u==forbidden) take[u]=NEG;
    }
    return max(take[0],skip[0]);
};
long long population=max(solve(cycleU),solve(cycleV));
cout<<fixed<<setprecision(1)<<population*multiplier<<'\n';
    return 0;
}
