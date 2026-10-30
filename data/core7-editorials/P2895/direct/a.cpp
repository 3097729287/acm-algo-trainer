#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const int size=303,inf=1000000000;vector<vector<int>>destroy(size,vector<int>(size,inf));int m;cin>>m;
int dr[]={0,1,-1,0,0},dc[]={0,0,0,1,-1};
for(int i=0;i<m;++i){int x,y,t;cin>>x>>y>>t;for(int d=0;d<5;++d){int nx=x+dr[d],ny=y+dc[d];if(0<=nx&&nx<size&&0<=ny&&ny<size)destroy[nx][ny]=min(destroy[nx][ny],t);}}
if(destroy[0][0]==0){cout<<-1<<'\n';return 0;}
vector<vector<int>>distance(size,vector<int>(size,-1));queue<pair<int,int>>todo;todo.push({0,0});distance[0][0]=0;
while(!todo.empty()){auto [x,y]=todo.front();todo.pop();if(destroy[x][y]==inf){cout<<distance[x][y]<<'\n';return 0;}
    for(int d=1;d<5;++d){int nx=x+dr[d],ny=y+dc[d],arrival=distance[x][y]+1;
        // 等于毁灭时刻也来不及，只有严格更早才能进入。
        if(0<=nx&&nx<size&&0<=ny&&ny<size&&distance[nx][ny]==-1&&arrival<destroy[nx][ny]){distance[nx][ny]=arrival;todo.push({nx,ny});}
    }
}
cout<<-1<<'\n';
    return 0;
}
