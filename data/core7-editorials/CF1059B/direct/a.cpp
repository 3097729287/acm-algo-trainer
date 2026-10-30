#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<string>target(n),painted(n,string(m,'.'));for(auto &row:target)cin>>row;
for(int r=1;r+1<n;++r)for(int c=1;c+1<m;++c){bool allowed=true;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy)if((dx||dy)&&target[r+dx][c+dy]!='#')allowed=false;
    if(!allowed)continue;
    // 中心不涂，也不要求它在目标图中必须为空。
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy)if(dx||dy)painted[r+dx][c+dy]='#';
}
cout<<(painted==target?"YES":"NO")<<'\n';
    return 0;
}
