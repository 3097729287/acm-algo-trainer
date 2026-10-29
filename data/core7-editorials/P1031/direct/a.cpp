#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>a(n);long long total=0;
for(auto &x:a){cin>>x;total+=x;}long long average=total/n,balance=0;int answer=0;
for(int i=0;i+1<n;++i){balance+=a[i]-average;answer+=balance!=0;}
cout<<answer<<'\n';
    return 0;
}
