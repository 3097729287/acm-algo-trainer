#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m,n;cin>>m>>n;vector<vector<char>>removed(m);for(int d=0;d<m;++d)removed[d].assign(1<<d,false);
for(int z=0,d,j;z<n;++z){cin>>d>>j;removed[d-1][j-1]=true;}
vector<int>step(m-1);step[m-2]=2;if(m>=3)step[m-3]=3;for(int d=m-4;d>=0;--d)step[d]=2*step[d+1];
int span=accumulate(step.begin(),step.end(),0);vector<string>canvas(span+1,string(2*span+1,' '));
function<void(int,int,int,int)>draw=[&](int d,int index,int y,int x){
    if(removed[d][index])return;canvas[y][x]='o';if(d+1==m)return;
    for(int side=0;side<2;++side){int child=2*index+side;if(removed[d+1][child])continue;
        int sign=side?1:-1,len=step[d];for(int t=1;t<len;++t)canvas[y+t][x+sign*t]=side?'\\':'/';
        draw(d+1,child,y+len,x+sign*len);
    }
};draw(0,0,0,span);for(const auto &row:canvas)cout<<row<<'\n';
    return 0;
}
