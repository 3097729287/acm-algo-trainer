#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>child(n);vector<int>indegree(n);vector<long long>cost(n);
for(int row=0;row<n;++row){int u,count;cin>>u;--u;cin>>cost[u]>>count;while(count--){int v;cin>>v;--v;child[u].push_back(v);++indegree[v];}}
int root=0;while(indegree[root]) ++root;vector<int>order={root};
for(size_t pos=0;pos<order.size();++pos) for(int v:child[order[pos]]) order.push_back(v);
const long long INF=1000000000000000LL;
vector<long long>guard(n),covered(n),waiting(n);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];guard[u]=cost[u];long long base=0,extra=INF;
    for(int v:child[u]){
        guard[u]+=min({guard[v],covered[v],waiting[v]});
        long long best=min(guard[v],covered[v]);base+=best;
        extra=min(extra,guard[v]-best);
        waiting[u]=min(INF,waiting[u]+covered[v]);
    }
    covered[u]=extra==INF?INF:base+extra;
}
cout<<min(guard[root],covered[root])<<'\n';
    return 0;
}
