#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<int> a(2*n); for(int i=0;i<n;++i){cin>>a[i];a[i+n]=a[i];}
vector<long long> prefix(2*n+1);
for(int i=0;i<2*n;++i) prefix[i+1]=prefix[i]+a[i];
vector<vector<long long>> low(2*n,vector<long long>(2*n)),high=low;
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=2*n;++l){
        int r=l+length-1; long long sum=prefix[r+1]-prefix[l];
        low[l][r]=LLONG_MAX/4;
        for(int k=l;k<r;++k){
            low[l][r]=min(low[l][r],low[l][k]+low[k+1][r]+sum);
            high[l][r]=max(high[l][r],high[l][k]+high[k+1][r]+sum);
        }
    }
}
long long minimum=LLONG_MAX,maximum=0;
for(int l=0;l<n;++l){minimum=min(minimum,low[l][l+n-1]);maximum=max(maximum,high[l][l+n-1]);}
cout<<minimum<<'\n'<<maximum<<'\n';
    return 0;
}
