#include <bits/stdc++.h>
using namespace std;
int main(){int n;long long m;cin>>n>>m;vector<long long>a(n);for(auto &x:a)cin>>x;int ans=0;
for(int i=0;i<n;i++){long long l=0,r=0;for(int j=0;j<=i;j++)l+=a[j];for(int j=i;j<n;j++)r+=a[j];if((l-r)%m==0)ans++;}cout<<ans<<'\n';}
