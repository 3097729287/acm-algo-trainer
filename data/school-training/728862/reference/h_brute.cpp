#include <bits/stdc++.h>
using namespace std;
int main(){int n,a,b,c;cin>>n>>a>>b>>c;int ans=-1;for(int x=0;x*a<=n;++x)for(int y=0;x*a+y*b<=n;++y){int rest=n-x*a-y*b;if(rest%c==0)ans=max(ans,x+y+rest/c);}cout<<ans<<'\n';}
