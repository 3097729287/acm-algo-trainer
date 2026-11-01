#include <bits/stdc++.h>
using namespace std;
struct DSU{
    vector<int>parent,size;
    // 这里的n表示0至n-1共n个对象。
    explicit DSU(int n):parent(n),size(n,1){iota(parent.begin(),parent.end(),0);}
    int root(int u){while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;}
    bool merge(int u,int v){u=root(u);v=root(v);if(u==v)return false;
        if(size[u]<size[v])swap(u,v);parent[v]=u;size[u]+=size[v];return true;
    }
};
struct Edge{int u,v;long long w;};

struct TreeMax{
    int n,levels;vector<int>depth;vector<vector<int>>up;vector<vector<long long>>largest;
    explicit TreeMax(const vector<vector<pair<int,long long>>> &g):n(g.size()),levels(1),depth(n,-1){
        while((1LL<<levels)<=n)++levels;
        up.assign(levels,vector<int>(n));largest.assign(levels,vector<long long>(n,LLONG_MIN));
        for(int root=0;root<n;++root)if(depth[root]==-1){
            vector<int>order{root};depth[root]=0;up[0][root]=root;
            for(size_t at=0;at<order.size();++at){int u=order[at];
                for(auto [v,w]:g[u])if(depth[v]==-1){depth[v]=depth[u]+1;up[0][v]=u;largest[0][v]=w;order.push_back(v);}
            }
        }
        // 两段等长上行路径拼成更长一段，同时合并最大边。
        for(int k=1;k<levels;++k)for(int v=0;v<n;++v){
            int middle=up[k-1][v];up[k][v]=up[k-1][middle];largest[k][v]=max(largest[k-1][v],largest[k-1][middle]);
        }
    }
    long long query(int u,int v)const{
        if(u==v)return 0;long long answer=LLONG_MIN;if(depth[u]<depth[v])swap(u,v);
        int delta=depth[u]-depth[v];for(int k=0;k<levels;++k)if(delta>>k&1){answer=max(answer,largest[k][u]);u=up[k][u];}
        if(u==v)return answer;
        for(int k=levels-1;k>=0;--k)if(up[k][u]!=up[k][v]){
            answer=max({answer,largest[k][u],largest[k][v]});u=up[k][u];v=up[k][v];
        }
        return max({answer,largest[0][u],largest[0][v]});
    }
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
vector<int>order(m);iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return edges[a].w<edges[b].w;});
DSU dsu(n);vector<char>used(m);vector<vector<pair<int,long long>>>tree(n);
for(int i:order){const auto &e=edges[i];if(dsu.merge(e.u,e.v)){used[i]=true;tree[e.u].push_back({e.v,e.w});tree[e.v].push_back({e.u,e.w});}}
TreeMax paths(tree);for(int i=0;i<m;++i)if(!used[i])cout<<paths.query(edges[i].u,edges[i].v)<<'\n';
    return 0;
}
