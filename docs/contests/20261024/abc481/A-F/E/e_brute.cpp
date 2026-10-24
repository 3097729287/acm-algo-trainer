#include <bits/stdc++.h>
using namespace std;
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<pair<long long,long long>>p(n);for(auto&[x,y]:p)cin>>x>>y;int ans=1;
// 枚举将边界从每条星光射线旁稍稍转开的两侧，不排序、不使用窗口。
for(auto[x,y]:p){int a=0,b=0;for(auto[u,v]:p){long long z=x*v-y*u;a+=z>0;b+=z<0;}ans=max({ans,a+1,b+1});}cout<<ans<<'\n';}}
