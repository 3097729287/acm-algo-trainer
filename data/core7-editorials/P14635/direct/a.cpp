#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long money;cin>>n>>money;vector<long long>single(n);long long pair_price=LLONG_MAX;
for(auto &x:single){long long y;cin>>x>>y;pair_price=min(pair_price,x+y);}sort(single.begin(),single.end());
long long prefix=0,answer=0;
// r 种各留一颗单糖，其余全部按最便宜的对价购买。
for(int r=0;r<=n;++r){if(r>0)prefix+=single[r-1];if(prefix>money)break;answer=max(answer,(long long)r+2*((money-prefix)/pair_price));}
cout<<answer<<'\n';
    return 0;
}
