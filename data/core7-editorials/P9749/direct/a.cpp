#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long d;cin>>n>>d;vector<long long>road(max(0,n-1)),price(n);
for(auto &x:road)cin>>x;for(auto &x:price)cin>>x;
long long distance=0,litres=0,cheapest=LLONG_MAX,answer=0;
for(int i=0;i+1<n;++i){
    cheapest=min(cheapest,price[i]);distance+=road[i];long long need=(distance+d-1)/d;
    answer+=(need-litres)*cheapest;litres=need;
}
cout<<answer<<'\n';
    return 0;
}
