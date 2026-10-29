#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>head(n),knight(m);for(int &x:head)cin>>x;for(int &x:knight)cin>>x;
sort(head.begin(),head.end());sort(knight.begin(),knight.end());int i=0;long long cost=0;
for(int ability:knight)if(i<n&&ability>=head[i]){cost+=ability;++i;}
if(i==n)cout<<cost<<'\n';else cout<<"you died!\n";
    return 0;
}
