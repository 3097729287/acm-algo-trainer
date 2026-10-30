#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;const int LIMIT=1000,SIZE=1001;vector<vector<int>>difference(SIZE,vector<int>(SIZE));
while(n--){int x1,y1,x2,y2;cin>>x1>>y1>>x2>>y2;++difference[x1][y1];--difference[x2][y1];--difference[x1][y2];++difference[x2][y2];}
int area=0;
for(int x=0;x<LIMIT;++x)for(int y=0;y<LIMIT;++y){
    if(x>0)difference[x][y]+=difference[x-1][y];if(y>0)difference[x][y]+=difference[x][y-1];
    if(x>0&&y>0)difference[x][y]-=difference[x-1][y-1];area+=difference[x][y]==k;
}
cout<<area<<'\n';
    return 0;
}
