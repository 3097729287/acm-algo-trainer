#include <bits/stdc++.h>
using namespace std;
int main(){int n,k;cin>>n>>k;vector<int>a(n);for(int&v:a)cin>>v;int best=INT_MAX,ans=1;for(int l=0;l+k<=n;++l){int s=0;for(int r=l;r<l+k;++r)s+=a[r];if(s<best){best=s;ans=l+1;}}cout<<ans<<'\n';}
