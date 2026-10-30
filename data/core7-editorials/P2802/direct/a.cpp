#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>grid(n,vector<int>(m));int sx=0,sy=0;
for(int i=0;i<n;++i)for(int j=0;j<m;++j){cin>>grid[i][j];if(grid[i][j]==2){sx=i;sy=j;}}
vector<vector<vector<int>>>distance(n,vector<vector<int>>(m,vector<int>(7,-1)));
queue<tuple<int,int,int>>todo;todo.push({sx,sy,6});distance[sx][sy][6]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y,hp]=todo.front();todo.pop();int steps=distance[x][y][hp];
    if(grid[x][y]==3){cout<<steps<<'\n';return 0;}if(hp==1)continue;
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(nx<0||nx>=n||ny<0||ny>=m||grid[nx][ny]==0)continue;
        int next_hp=hp-1; // 先扣血，存活后才能拾取补给。
        if(grid[nx][ny]==4)next_hp=6;
        if(distance[nx][ny][next_hp]==-1){distance[nx][ny][next_hp]=steps+1;todo.push({nx,ny,next_hp});}
    }
}
cout<<-1<<'\n';
    return 0;
}
