#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,q;cin>>n>>q;const int LOG=18;
vector<int>diameter(n+1),stack;vector<vector<int>>up(LOG,vector<int>(n+1));
vector<vector<long long>>cost(LOG,vector<long long>(n+1));
for(int i=1;i<=n;++i){
    cin>>diameter[i]>>cost[0][i];
    while(!stack.empty()&&diameter[stack.back()]<diameter[i]){up[0][stack.back()]=i;stack.pop_back();}
    stack.push_back(i);
}
for(int j=1;j<LOG;++j)for(int u=1;u<=n;++u){
    int middle=up[j-1][u];up[j][u]=up[j-1][middle];cost[j][u]=cost[j-1][u]+cost[j-1][middle];
}
while(q--){
    int u;long long water;cin>>u>>water;
    for(int j=LOG-1;j>=0&&u!=0;--j)if(cost[j][u]<water){water-=cost[j][u];u=up[j][u];}
    cout<<u<<'\n';
}
    return 0;
}
