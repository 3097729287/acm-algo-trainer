#include <bits/stdc++.h>
using namespace std;
// 小规模物理模拟：每个整时刻枚举所有人的左右移动与接触传播。
int main(){int n;cin>>n;vector<int>x(n);for(int &v:x)cin>>v;
if(n==1){cout<<0<<'\n';return 0;}
int base=x.back()+3;for(int first=0;first<n;first++){
set<pair<vector<int>,int>> states;states.insert({x,1<<first});int answer=-1;
for(int t=1;t<=x.back()/2+1&&answer==-1;t++){
set<pair<vector<int>,int>> next;
for(const auto &state:states)for(int moves=0;moves<(1<<n);moves++){
vector<int>p=state.first;bool valid=true;for(int i=0;i<n;i++){p[i]+=(moves>>i&1)?1:-1;if(p[i]<0||p[i]>=base)valid=false;}
if(!valid){continue;}int mask=state.second;
for(int repeat=0;repeat<n;repeat++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)if(p[i]==p[j]&&(mask>>i&1))mask|=1<<j;
if(mask==(1<<n)-1){answer=t;break;}next.insert({p,mask});
}states.swap(next);}
cout<<answer<<'\n';}}
