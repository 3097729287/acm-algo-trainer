#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int r,c,k;cin>>r>>c>>k;vector<string>g(r);for(string &s:g)cin>>s;int answer=0;
for(int i=0;i<r;++i){int length=0;for(int j=0;j<c;++j){length=g[i][j]=='.'?length+1:0;if(length>=k)++answer;}}
if(k>1)for(int j=0;j<c;++j){int length=0;for(int i=0;i<r;++i){length=g[i][j]=='.'?length+1:0;if(length>=k)++answer;}}
cout<<answer<<'\n';
    return 0;
}
