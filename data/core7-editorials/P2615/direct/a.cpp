#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>> a(n,vector<int>(n));
int r=0,c=n/2;
for(int x=1;x<=n*n;++x){a[r][c]=x;
    int nr=(r-1+n)%n,nc=(c+1)%n;
    if(a[nr][nc])r=(r+1)%n;else {r=nr;c=nc;}
}
for(auto &row:a){for(int j=0;j<n;++j)cout<<row[j]<<(j+1==n?'\n':' ');}
    return 0;
}
