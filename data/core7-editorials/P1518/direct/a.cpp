#include <bits/stdc++.h>
using namespace std;
struct Actor{int r,c,d;};vector<string>g;
int code(const Actor &a){return (a.r*10+a.c)*4+a.d;}
void step(Actor &a){
    int dr[4]={-1,0,1,0},dc[4]={0,1,0,-1};int r=a.r+dr[a.d],c=a.c+dc[a.d];
    if(r<0||r>=10||c<0||c>=10||g[r][c]=='*')a.d=(a.d+1)%4;else{a.r=r;a.c=c;}
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
g.resize(10);Actor farmer{},cow{};for(int i=0;i<10;++i){cin>>g[i];for(int j=0;j<10;++j){if(g[i][j]=='F')farmer={i,j,0};if(g[i][j]=='C')cow={i,j,0};}}
vector<bool>seen(160000);int minutes=0;
while(true){
    if(farmer.r==cow.r&&farmer.c==cow.c){cout<<minutes<<'\n';break;}
    int state=code(farmer)*400+code(cow);if(seen[state]){cout<<0<<'\n';break;}seen[state]=true;
    step(farmer);step(cow);++minutes;
}
    return 0;
}
