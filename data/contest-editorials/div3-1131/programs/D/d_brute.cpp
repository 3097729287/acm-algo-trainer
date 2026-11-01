#include <bits/stdc++.h>
using namespace std;
// 直接枚举锁定子集和方向，在平移等价类上做字典序最短路。
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;int low=*min_element(a.begin(),a.end());for(int &v:a)v-=low;
using Cost=pair<int,int>;using Entry=pair<Cost,vector<int>>;map<vector<int>,Cost>dist;priority_queue<Entry,vector<Entry>,greater<Entry>>q;dist[a]={0,0};q.push({{0,0},a});
while(!q.empty()){auto entry=q.top();q.pop();Cost cost=entry.first;auto current=entry.second;if(dist[current]!=cost)continue;if(*max_element(current.begin(),current.end())==0){cout<<cost.first<<' '<<cost.second<<'\n';break;}
for(int mask=1;mask<(1<<n)-1;mask++)for(int dir:{-1,1}){auto next=current;for(int i=0;i<n;i++)if(!(mask>>i&1))next[i]+=dir;int mn=*min_element(next.begin(),next.end());for(int &v:next)v-=mn;Cost nc={cost.first+__builtin_popcount((unsigned)mask),cost.second+1};if(!dist.count(next)||nc<dist[next]){dist[next]=nc;q.push({nc,next});}}}
}}
