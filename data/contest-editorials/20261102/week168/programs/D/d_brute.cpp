#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;cin>>n>>m;vector<long long>a(n);for(auto &x:a)cin>>x;vector<bool>used(n);int p=0;long long ans=0;
for(int i=0;i<m;i++){long long d;cin>>d;p=(p+d)%n;while(used[p])p=(p+1)%n;used[p]=true;ans+=a[p];}cout<<ans<<' '<<p+1<<'\n';}
