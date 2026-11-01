#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;vector<int>a(n);int total=0;for(int&v:a){cin>>v;total+=v;}int ans=n;for(int mask=0;mask<(1<<n);++mask){int s=0,c=0;for(int i=0;i<n;++i)if(mask>>i&1){s+=a[i];++c;}if(s>total-s)ans=min(ans,c);}cout<<ans<<'\n';}
