#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,q;cin>>n>>q;vector<int>a(n*n);for(int &x:a)cin>>x;sort(a.begin(),a.end());
while(q--){int v;cin>>v;int count=a.end()-lower_bound(a.begin(),a.end(),v);cout<<min(n,count)<<'\n';}
    return 0;
}
