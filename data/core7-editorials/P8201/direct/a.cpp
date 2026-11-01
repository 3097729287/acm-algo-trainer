#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;const int levels=20;vector<int>weight(n+1),values;for(int i=1;i<=n;++i){cin>>weight[i];values.push_back(weight[i]);}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());vector<int>rank(n+1);for(int i=1;i<=n;++i) rank[i]=lower_bound(values.begin(),values.end(),weight[i])-values.begin();
vector<int>head(n+1,-1),to(2*(n-1)),next(2*(n-1));int edges=0;auto add=[&](int x,int y){to[edges]=y;next[edges]=head[x];head[x]=edges++;};for(int i=1,x,y;i<n;++i){cin>>x>>y;add(x,y);add(y,x);}
vector<array<int,levels>>up(n+1);vector<int>depth(n+1),prefix(n+1),order={1};depth[1]=1;prefix[1]=weight[1];for(int at=0;at<(int)order.size();++at){int u=order[at];for(int e=head[u];e!=-1;e=next[e]){int v=to[e];if(v==up[u][0]) continue;up[v][0]=u;depth[v]=depth[u]+1;prefix[v]=prefix[u]^weight[v];for(int j=1;j<levels;++j) up[v][j]=up[up[v][j-1]][j-1];order.push_back(v);}}
auto lca=[&](int a,int b){if(depth[a]<depth[b]) swap(a,b);int difference=depth[a]-depth[b];for(int j=0;j<levels;++j) if(difference>>j&1) a=up[a][j];if(a==b) return a;for(int j=levels-1;j>=0;--j) if(up[a][j]!=up[b][j]){a=up[a][j];b=up[b][j];}return up[a][0];};
vector<int>queryHead(n+1,-1),queryId,queryNext,target(m),minimumDepth(m);vector<char>answer(m);queryId.reserve(2*m);queryNext.reserve(2*m);auto attach=[&](int u,int id){queryId.push_back(id);queryNext.push_back(queryHead[u]);queryHead[u]=queryId.size()-1;};
for(int i=0,a,b,k;i<m;++i){cin>>a>>b>>k;int c=lca(a,b),need=prefix[a]^prefix[b]^weight[c]^k;auto it=lower_bound(values.begin(),values.end(),need);if(it==values.end()||*it!=need) continue;target[i]=it-values.begin();minimumDepth[i]=depth[c];attach(a,i);attach(b,i);}
vector<int>last(values.size()),saved(n+1),stack={1};while(!stack.empty()){int event=stack.back();stack.pop_back();if(event<0){int u=-event;last[rank[u]]=saved[u];continue;}int u=event;saved[u]=last[rank[u]];last[rank[u]]=u;for(int e=queryHead[u];e!=-1;e=queryNext[e]){int id=queryId[e],v=last[target[id]];if(v&&depth[v]>=minimumDepth[id]) answer[id]=true;}stack.push_back(-u);for(int e=head[u];e!=-1;e=next[e]) if(to[e]!=up[u][0]) stack.push_back(to[e]);}
for(char yes:answer) cout<<(yes?"Yes":"No")<<'\n';
    return 0;
}
