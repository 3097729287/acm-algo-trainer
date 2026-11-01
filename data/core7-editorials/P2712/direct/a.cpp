#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>positions;vector<vector<int>>watched(501),graph(501);vector<int>camera(501),indegree(501);
for(int i=0;i<n;++i){int x,m;cin>>x>>m;camera[x]=1;positions.push_back(x);while(m--){int y;cin>>y;watched[x].push_back(y);}}
for(int x:positions)for(int y:watched[x])if(x!=y&&camera[y]){graph[x].push_back(y);++indegree[y];}
queue<int>ready;for(int x:positions)if(!indegree[x])ready.push(x);int removed=0;
while(!ready.empty()){int x=ready.front();ready.pop();++removed;for(int y:graph[x])if(--indegree[y]==0)ready.push(y);}
if(removed==n)cout<<"YES\n";else cout<<n-removed<<'\n';
    return 0;
}
