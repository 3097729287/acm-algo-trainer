#include <bits/stdc++.h>
using namespace std;
vector<string>canvas;
void draw(int row,int column,int height){
    if(height==2){
        canvas[row][column+1]='/';canvas[row][column+2]='\\';
        canvas[row+1][column]='/';canvas[row+1][column+1]='_';
        canvas[row+1][column+2]='_';canvas[row+1][column+3]='\\';return;
    }
    int half=height/2;
    draw(row,column+half,half);draw(row+half,column,half);draw(row+half,column+height,half);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;int height=1<<n;canvas.assign(height,string(2*height,' '));draw(0,0,height);
for(auto line:canvas){while(!line.empty()&&line.back()==' ')line.pop_back();cout<<line<<'\n';}
    return 0;
}
