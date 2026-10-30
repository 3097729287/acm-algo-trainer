#include <bits/stdc++.h>
using namespace std;
void cover(int row,int column,int size,int hole_x,int hole_y){
    if(size==1)return;int half=size/2;
    int q=(hole_x>=row+half)*2+(hole_y>=column+half);
    int x[4]={row+half-1,row+half-1,row+half,row+half};
    int y[4]={column+half-1,column+half,column+half-1,column+half};
    int corner=3-q;cout<<x[corner]<<' '<<y[corner]<<' '<<q+1<<'\n';
    for(int part=0;part<4;++part){
        int hx=part==q?hole_x:x[part],hy=part==q?hole_y:y[part];
        cover(row+(part/2)*half,column+(part%2)*half,half,hx,hy);
    }
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int k,x,y;cin>>k>>x>>y;cover(1,1,1<<k,x,y);
    return 0;
}
