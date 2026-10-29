#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');
    return 0;
}
