#include <bits/stdc++.h>
using namespace std;
// 直接枚举 N 的每个约数，以乘一个约数作为一条普通 BFS 边。
int main(){long long n;int m;cin>>n>>m;vector<long long>divs;for(long long d=1;d*d<=n;d++)if(n%d==0){divs.push_back(d);if(d*d!=n)divs.push_back(n/d);}
vector<int>dist(m,-1);queue<int>q;dist[1%m]=0;q.push(1%m);while(!q.empty()){int r=q.front();q.pop();for(long long d:divs){int to=r*(d%m)%m;if(dist[to]<0){dist[to]=dist[r]+1;q.push(to);}}}
for(int d:dist)cout<<(d<0?-1:max(1,d))<<'\n';}
