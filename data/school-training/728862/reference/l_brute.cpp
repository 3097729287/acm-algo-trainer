#include <bits/stdc++.h>
using namespace std;
int main(){int n;long long t;cin>>n>>t;vector<int>a(n);for(int&v:a)cin>>v;int ans=0;for(int l=0;l<n;++l){long long s=0;for(int r=l;r<n;++r){s+=a[r];if(s<=t)ans=max(ans,r-l+1);}}cout<<ans<<'\n';}
