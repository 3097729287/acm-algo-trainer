#include <bits/stdc++.h>
using namespace std;
int main(){int n,k;cin>>n>>k;vector<int>a(n);for(int&x:a)cin>>x;set<pair<long long,long long>>xs;
for(int i=0;i<n-1;i++)if(min(a[i],a[i+1])<=k&&k<=max(a[i],a[i+1])){
long long den=a[i+1]-a[i],num=1LL*i*den+k-a[i];if(den<0)den=-den,num=-num;long long g=gcd(abs(num),den);xs.insert({num/g,den/g});}
cout<<xs.size()<<'\n';}
