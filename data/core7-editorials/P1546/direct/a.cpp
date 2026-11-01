#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<long long>>cost(n,vector<long long>(n));for(auto &row:cost)for(auto &w:row)cin>>w;
const long long INF=(1LL<<60);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long long answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=best[u];
    // 只比较新铺这条线的费用，不能加到根的距离。
    for(int v=0;v<n;++v)if(!used[v])best[v]=min(best[v],cost[u][v]);
}cout<<answer<<'\n';
    return 0;
}
