#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<array<int,3>>p(n+1);string colors="WBR";
for(int i=1;i<=n;++i){string row;cin>>row;p[i]=p[i-1];
    for(char ch:row)for(int c=0;c<3;++c)p[i][c]+=ch!=colors[c];
}
int answer=n*m;for(int a=1;a<n-1;++a)for(int b=a+1;b<n;++b)
    answer=min(answer,p[a][0]+p[b][1]-p[a][1]+p[n][2]-p[b][2]);
cout<<answer<<'\n';
    return 0;
}
