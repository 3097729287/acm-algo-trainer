#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<string>grid(n);vector<pair<int,int>>port[26];int sx=0,sy=0;
for(int i=0;i<n;++i){cin>>grid[i];for(int j=0;j<m;++j){char c=grid[i][j];if(c=='@'){sx=i;sy=j;}if('A'<=c&&c<='Z')port[c-'A'].push_back({i,j});}}
vector<vector<int>>distance(n,vector<int>(m,-1));queue<pair<int,int>>todo;todo.push({sx,sy});distance[sx][sy]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y]=todo.front();todo.pop();if(grid[x][y]=='='){cout<<distance[x][y]<<'\n';return 0;}
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(nx<0||nx>=n||ny<0||ny>=m||grid[nx][ny]=='#')continue;
        char c=grid[nx][ny];
        if('A'<=c&&c<='Z'){
            auto &ends=port[c-'A'];pair<int,int>entered={nx,ny};auto destination=(ends[0]==entered?ends[1]:ends[0]);
            nx=destination.first;ny=destination.second; // 同一次行动只传送一次。
        }
        if(distance[nx][ny]==-1){distance[nx][ny]=distance[x][y]+1;todo.push({nx,ny});}
    }
}
cout<<-1<<'\n';
    return 0;
}
