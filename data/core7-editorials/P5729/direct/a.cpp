#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int w,x,h,q; cin >> w >> x >> h >> q;
bool removed[21][21][21]={};
while(q--){int a,b,c,d,e,f;cin>>a>>b>>c>>d>>e>>f;
    for(int i=a;i<=d;++i)for(int j=b;j<=e;++j)for(int k=c;k<=f;++k)removed[i][j][k]=true;
}
int answer=0;for(int i=1;i<=w;++i)for(int j=1;j<=x;++j)for(int k=1;k<=h;++k)answer+=!removed[i][j][k];
cout << answer << '\n';
    return 0;
}
