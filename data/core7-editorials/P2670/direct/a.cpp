#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<string>g(n);for(string &s:g)cin>>s;
for(int i=0;i<n;++i){for(int j=0;j<m;++j){
    if(g[i][j]=='*'){cout<<'*';continue;}
    int count=0;
    for(int dr=-1;dr<=1;++dr)for(int dc=-1;dc<=1;++dc){
        if(dr==0&&dc==0)continue;
        int r=i+dr,c=j+dc;
        if(r>=0&&r<n&&c>=0&&c<m&&g[r][c]=='*')++count;
    }
    cout<<count;
}cout<<'\n';}
    return 0;
}
