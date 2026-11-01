#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long l,r;cin>>n>>l>>r;vector<int>a;for(int i=0;i<n;++i){int v;cin>>v;if(v)a.push_back(v);}
// 零系数全被删掉时，只有零可表示。
if(a.empty()){cout<<0<<'\n';return 0;}int m=*min_element(a.begin(),a.end());
const long long INF=(1LL<<62);vector<long long>dist(m,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[0]=0;pq.push({0,0});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(int value:a){int v=(u+value)%m;if(du+value<dist[v]){dist[v]=du+value;pq.push({dist[v],v});}}
}auto count=[&](long long X){long long answer=0;for(long long d:dist)if(d!=INF&&d<=X)answer+=(X-d)/m+1;return answer;};
cout<<count(r)-count(l-1)<<'\n';
    return 0;
}
