#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(tests--){int n,m;cin>>n>>m;vector<string>grid(n);for(auto &row:grid)cin>>row;bool possible=true;
    for(int r=0;r<n;++r)for(int c=0;c<m;++c)if(grid[r][c]=='B')for(int d=0;d<4;++d){int nr=r+dr[d],nc=c+dc[d];if(nr<0||nr>=n||nc<0||nc>=m)continue;if(grid[nr][nc]=='G')possible=false;else if(grid[nr][nc]=='.')grid[nr][nc]='#';}
    vector<vector<int>>seen(n,vector<int>(m));queue<pair<int,int>>todo;
    if(grid[n-1][m-1]!='#'){seen[n-1][m-1]=1;todo.push({n-1,m-1});}
    while(!todo.empty()){auto [r,c]=todo.front();todo.pop();for(int d=0;d<4;++d){int nr=r+dr[d],nc=c+dc[d];if(nr>=0&&nr<n&&nc>=0&&nc<m&&grid[nr][nc]!='#'&&!seen[nr][nc]){seen[nr][nc]=1;todo.push({nr,nc});}}}
    for(int r=0;r<n;++r)for(int c=0;c<m;++c)if((grid[r][c]=='G'&&!seen[r][c])||(grid[r][c]=='B'&&seen[r][c]))possible=false;
    cout<<(possible?"Yes":"No")<<'\n';
}
    return 0;
}
