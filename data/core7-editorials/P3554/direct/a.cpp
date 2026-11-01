#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
vector<int>need(n);
auto possible=[&](int capacity){
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos],required=0;
        for(int v:g[u]) if(parent[v]==u) required+=need[v]+1;
        need[u]=max(0,required-capacity);
    }
    return need[0]==0;
};
int low=0,high=n;
while(low<high){int mid=low+(high-low)/2;if(possible(mid)) high=mid;else low=mid+1;}
cout<<low<<'\n';
    return 0;
}
