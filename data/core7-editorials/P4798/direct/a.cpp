#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const long long MOD=1000007;int n;cin>>n;vector<int>a(n+1),before(n+1);int largest=0;
for(int i=1;i<=n;++i){cin>>a[i];before[i]=largest;largest=max(largest,a[i]);}
vector<long long>ways(n+2,1);long long answer=1;
for(int remaining=0;remaining<n;++remaining){
    int i=n-remaining;answer=(answer+(a[i]-1LL)*ways[before[i]])%MOD;
    for(int existing=0;existing<=n-remaining-2;++existing) ways[existing]=(existing*ways[existing]+ways[existing+1])%MOD;
}
cout<<answer<<'\n';
    return 0;
}
