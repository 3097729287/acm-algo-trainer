#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long A;int B;cin>>A>>B;vector<vector<int>>price(B,vector<int>(B));for(auto &row:price)for(int &v:row)cin>>v;
vector<long long>best(B,A);vector<char>used(B);long long answer=0;
// 虚拟商店已经加入，所有原价边就是初始候选。
for(int step=0;step<B;++step){int u=-1;for(int v=0;v<B;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=best[u];
    for(int v=0;v<B;++v)if(!used[v]&&price[u][v]>0)best[v]=min(best[v],(long long)price[u][v]);
}cout<<answer<<'\n';
    return 0;
}
