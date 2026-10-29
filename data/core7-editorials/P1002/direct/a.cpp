#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,hx,hy;cin>>n>>m>>hx>>hy;bool blocked[21][21]={};
int dx[9]={0,1,1,-1,-1,2,2,-2,-2};int dy[9]={0,2,-2,2,-2,1,-1,1,-1};
for(int i=0;i<9;++i){int x=hx+dx[i],y=hy+dy[i];if(0<=x&&x<=n&&0<=y&&y<=m)blocked[x][y]=true;}
long long f[21][21]={};
for(int x=0;x<=n;++x)for(int y=0;y<=m;++y){
    if(blocked[x][y])continue;
    if(x==0&&y==0){f[x][y]=1;continue;} // 原点有一个空走法
    if(x>0)f[x][y]+=f[x-1][y];if(y>0)f[x][y]+=f[x][y-1];
}
cout<<f[n][m]<<'\n';
    return 0;
}
