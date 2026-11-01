#include <bits/stdc++.h>
using namespace std;
int main(){vector<string>s(5);for(auto &x:s)cin>>x;int ans=5;
int di[]={1,0,1,1},dj[]={0,1,1,-1};for(int x=0;x<5;x++)for(int y=0;y<5;y++)for(int d=0;d<4;d++){
int ex=x+4*di[d],ey=y+4*dj[d];if(ex<0||ex>=5||ey<0||ey>=5)continue;int cost=0;for(int t=0;t<5;t++)cost+=s[x+t*di[d]][y+t*dj[d]]=='.';ans=min(ans,cost);}cout<<ans<<'\n';}
