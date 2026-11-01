#include <bits/stdc++.h>
using namespace std;
struct Lift{
    int n,levels;vector<int>depth,order;vector<vector<int>>up;
    Lift(const vector<vector<int>> &g,int root):n(g.size()),levels(1),depth(n,-1){
        while((1LL<<levels)<=n)++levels;up.assign(levels,vector<int>(n,root));
        depth[root]=0;order.push_back(root);
        // 显式遍历次序，链形树也不消耗深递归调用栈。
        for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(depth[v]<0){
            depth[v]=depth[u]+1;up[0][v]=u;order.push_back(v);
        }}
        for(int j=1;j<levels;++j)for(int u=0;u<n;++u)up[j][u]=up[j-1][up[j-1][u]];
    }
    int lca(int u,int v)const{
        if(depth[u]<depth[v])swap(u,v);int gap=depth[u]-depth[v];
        for(int j=0;j<levels;++j)if((gap>>j)&1)u=up[j][u];
        if(u==v)return u;
        for(int j=levels-1;j>=0;--j)if(up[j][u]!=up[j][v]){u=up[j][u];v=up[j][v];}
        return up[0][u];
    }
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,q,k;cin>>n>>q>>k;vector<vector<int>>g(n);vector<vector<pair<int,int>>>weighted(n);
for(int i=1,u,v,w;i<n;++i){cin>>u>>v>>w;--u;--v;g[u].push_back(v);g[v].push_back(u);weighted[u].push_back({v,w});weighted[v].push_back({u,w});}
vector<int>count(n);vector<char>core(n);for(int i=0,u;i<k;++i){cin>>u;--u;count[u]=1;core[u]=true;}
Lift lift(g,0);vector<long long>rootDist(n);vector<int>edgeWeight(n);
for(int u:lift.order)for(auto [v,w]:weighted[u])if(lift.up[0][v]==u&&v!=u){rootDist[v]=rootDist[u]+w;edgeWeight[v]=w;}
long long total=0;for(int i=n-1;i>0;--i){int u=lift.order[i],p=lift.up[0][u];
    if(count[u]>0&&count[u]<k){total+=edgeWeight[u];core[u]=core[p]=true;}count[p]+=count[u];
}
vector<int>attach(n,-1),order;vector<long long>height(n);for(int u=0;u<n;++u)if(core[u]){attach[u]=u;order.push_back(u);}
for(size_t i=0;i<order.size();++i){int u=order[i];for(auto [v,w]:weighted[u])if(attach[v]<0){attach[v]=attach[u];height[v]=height[u]+w;order.push_back(v);}}
while(q--){int s,t;cin>>s>>t;--s;--t;int a=attach[s],b=attach[t],l=lift.lca(a,b);
    long long distance=rootDist[a]+rootDist[b]-2*rootDist[l];cout<<2*total+height[s]+height[t]-distance<<'\n';
}
    return 0;
}
