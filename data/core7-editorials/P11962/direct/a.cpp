#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>color(n+1,-1),order={1};color[1]=0;int count[2]={1,0};
// 显式遍历染色，不使用可能在深链上溢栈的递归。
for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(color[v]==-1){color[v]=color[u]^1;++count[color[v]];order.push_back(v);}}
for(int i=1;i<=n;++i)cout<<count[color[i]]<<(i==n?'\n':' ');
    return 0;
}
