#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a[5][5];for(auto &row:a)for(int &x:row)cin>>x;bool ok=false;
for(int i=0;i<5;++i){bool row=true,col=true;for(int j=0;j<5;++j){row&=a[i][j];col&=a[j][i];}ok|=row||col;}
bool d1=true,d2=true;for(int i=0;i<5;++i){d1&=a[i][i];d2&=a[i][4-i];}
cout<<(ok||d1||d2?"Yes":"No")<<'\n';
    return 0;
}
