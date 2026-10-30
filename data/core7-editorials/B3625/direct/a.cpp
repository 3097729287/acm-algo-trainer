#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<string>grid(n);for(auto &row:grid)cin>>row;vector<vector<bool>>visited(n,vector<bool>(m));
vector<pair<int,int>>todo={{0,0}};visited[0][0]=true;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y]=todo.back();todo.pop_back();if(x==n-1&&y==m-1){cout<<"Yes\n";return 0;}
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
        if(0<=nx&&nx<n&&0<=ny&&ny<m&&grid[nx][ny]=='.'&&!visited[nx][ny]){
            visited[nx][ny]=true;todo.push_back({nx,ny}); // 入栈时就标记，本题不撤销。
        }
    }
}
cout<<"No\n";
    return 0;
}
