#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n; long long a[21][21]={};
for(int i=1;i<=n;++i){
    a[i][1]=a[i][i]=1;
    for(int j=2;j<i;++j) a[i][j]=a[i-1][j-1]+a[i-1][j];
    for(int j=1;j<=i;++j) cout << a[i][j] << (j==i?'\n':' ');
}
    return 0;
}
