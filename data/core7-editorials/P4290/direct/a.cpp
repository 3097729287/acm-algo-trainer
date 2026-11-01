#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string alphabet="WING";
vector<int> count(4); for(int &x:count) cin>>x;
int parent[4][4]={};
for(int c=0;c<4;++c){
    for(int i=0;i<count[c];++i){string rule;cin>>rule;int x=alphabet.find(rule[0]),y=alphabet.find(rule[1]);parent[x][y]|=1<<c;}
}
int combine[16][16]={};
for(int a=0;a<16;++a) for(int b=0;b<16;++b){
    for(int x=0;x<4;++x) if(a>>x&1){
        for(int y=0;y<4;++y) if(b>>y&1) combine[a][b]|=parent[x][y];
    }
}
string s; cin>>s; int n=s.size();
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i) dp[i][i]=1<<alphabet.find(s[i]);
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){int r=l+length-1;for(int k=l;k<r;++k) dp[l][r]|=combine[dp[l][k]][dp[k+1][r]];}
}
if(!dp[0][n-1]) cout<<"The name is wrong!";
else for(int c=0;c<4;++c) if(dp[0][n-1]>>c&1) cout<<alphabet[c];
cout<<'\n';
    return 0;
}
