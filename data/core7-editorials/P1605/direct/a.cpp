#include <bits/stdc++.h>
using namespace std;
int rows,columns,obstacles,finish_x,finish_y;
bool blocked[7][7],visited[7][7];
long long walk(int x,int y){
    if(x==finish_x&&y==finish_y)return 1;
    visited[x][y]=true;long long answer=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
        if(1<=nx&&nx<=rows&&1<=ny&&ny<=columns&&!blocked[nx][ny]&&!visited[nx][ny])answer+=walk(nx,ny);
    }
    visited[x][y]=false; // 退出当前路线，把格子还给其它分支。
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>rows>>columns>>obstacles;int sx,sy;cin>>sx>>sy>>finish_x>>finish_y;
for(int i=0;i<obstacles;++i){int x,y;cin>>x>>y;blocked[x][y]=true;}
cout<<walk(sx,sy)<<'\n';
    return 0;
}
