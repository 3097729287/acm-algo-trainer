#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;double best=0;
for(int i=0;i<n;++i){int sum=0,low=11,high=-1;
    for(int j=0;j<m;++j){int x;cin>>x;sum+=x;low=min(low,x);high=max(high,x);}
    best=max(best,1.0*(sum-low-high)/(m-2));
}
cout<<fixed<<setprecision(2)<<best<<'\n';
    return 0;
}
