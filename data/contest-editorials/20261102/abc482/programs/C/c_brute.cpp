#include <bits/stdc++.h>
using namespace std;
int main(){int h,w,n,q;cin>>h>>w>>n>>q;vector<int>a(n),b(n);for(int i=0;i<n;i++)cin>>a[i]>>b[i];while(q--){int t,l,r,ans=0;cin>>t>>l>>r;for(int i=0;i<n;i++){int x=t==1?a[i]:b[i];ans+=l<=x&&x<=r;}cout<<ans<<'\n';}}
