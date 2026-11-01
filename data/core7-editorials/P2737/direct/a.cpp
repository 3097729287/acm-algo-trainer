#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>b(n);for(int &v:b)cin>>v;int m=*min_element(b.begin(),b.end());
const long long INF=(1LL<<60);vector<long long>dist(m,INF);dist[0]=0;
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;pq.push({0,0});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    // 加一个包装，状态只记录总量的余数。
    for(int value:b){int v=(u+value)%m;if(du+value<dist[v]){dist[v]=du+value;pq.push({dist[v],v});}}
}long long answer=0;for(long long d:dist){if(d==INF){cout<<0<<'\n';return 0;}answer=max(answer,d-m);}
cout<<answer<<'\n';
    return 0;
}
