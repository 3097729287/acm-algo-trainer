#include <bits/stdc++.h>
using namespace std;
int rows,columns;bool visited[8][8];long long directed_count=0;
void cut(int x,int y){
    if(x==0||x==rows||y==0||y==columns){++directed_count;return;}
    visited[x][y]=true;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(!visited[nx][ny])cut(nx,ny);}
    visited[x][y]=false; // 一条割线结束后恢复格点，供其它割线使用。
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>rows>>columns;
for(int x=1;x<rows;++x){
    visited[x][0]=true;cut(x,1);visited[x][0]=false;
    visited[x][columns]=true;cut(x,columns-1);visited[x][columns]=false;
}
for(int y=1;y<columns;++y){
    visited[0][y]=true;cut(1,y);visited[0][y]=false;
    visited[rows][y]=true;cut(rows-1,y);visited[rows][y]=false;
}
cout<<directed_count/2<<'\n';
    return 0;
}
