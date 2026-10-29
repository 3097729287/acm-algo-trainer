#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<vector<int>>g(n);
    for(int i=1;i<n;++i){int u,v;cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
    string target;cin>>target;vector<int>parent(n,-1),order(1,0),color(n,-1);parent[0]=-2;
    for(int i=0;i<(int)order.size();++i){int u=order[i];for(int v:g[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    bool ok=true;
    for(int at=n-1;at>=0&&ok;--at){int u=order[at],p=parent[u];
        if(color[u]<0)color[u]=p<0?0:target[p]=='B';
        int match=0;for(int v:g[u])if(parent[v]==u)match+=color[v]==(target[u]=='B');
        int need=((int)g[u].size()+1)/2;
        if(match>=need)continue;
        if(p<0||match+1<need){ok=false;break;}
        int forced=target[u]=='B';if(color[p]>=0&&color[p]!=forced){ok=false;break;}color[p]=forced;
    }
    if(!ok)cout<<"-1\n";else{for(int c:color)cout<<(c?'B':'W');cout<<'\n';}
}
    return 0;
}
