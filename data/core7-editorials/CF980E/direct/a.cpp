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
int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
Lift lift(g,n-1);vector<char>kept(n);kept[n-1]=true;int remaining=n-k-1;
for(int i=n-2;i>=0&&remaining;--i){if(kept[i])continue;int v=i;
    for(int j=lift.levels-1;j>=0;--j)if(!kept[lift.up[j][v]])v=lift.up[j][v];
    int need=lift.depth[i]-lift.depth[v]+1;if(need>remaining)continue;remaining-=need;
    for(int u=i;!kept[u];u=lift.up[0][u])kept[u]=true;
}
bool first=true;for(int u=0;u<n;++u)if(!kept[u]){if(!first)cout<<' ';first=false;cout<<u+1;}cout<<'\n';
    return 0;
}
