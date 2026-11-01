#include <bits/stdc++.h>
using namespace std;
int main(){int y;cin>>y;int ans=10000;for(int a=1;a<=9;++a)for(int b=0;b<=9;++b)for(int c=0;c<=9;++c)for(int d=0;d<=9;++d){set<int>s={a,b,c,d};int v=1000*a+100*b+10*c+d;if(s.size()==4&&v>y)ans=min(ans,v);}cout<<ans<<'\n';}
