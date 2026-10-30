#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int rows,columns;cin>>rows>>columns;vector<string>grid(rows);for(auto &row:grid)cin>>row;int ships=0;
int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
for(int r=0;r<rows;++r)for(int c=0;c<columns;++c)if(grid[r][c]=='#'){
    vector<pair<int,int>>todo={{r,c}};grid[r][c]='.';
    int min_r=r,max_r=r,min_c=c,max_c=c;
    for(size_t at=0;at<todo.size();++at){auto [x,y]=todo[at];
        min_r=min(min_r,x);max_r=max(max_r,x);min_c=min(min_c,y);max_c=max(max_c,y);
        for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
            if(0<=nx&&nx<rows&&0<=ny&&ny<columns&&grid[nx][ny]=='#'){grid[nx][ny]='.';todo.push_back({nx,ny});}
        }
    }
    // 四连通块全部位于外接矩形中，格数等于面积才说明没有缺口。
    if((long long)todo.size()!=1LL*(max_r-min_r+1)*(max_c-min_c+1)){cout<<"Bad placement.\n";return 0;}
    ++ships;
}
cout<<"There are "<<ships<<" ships.\n";
    return 0;
}
