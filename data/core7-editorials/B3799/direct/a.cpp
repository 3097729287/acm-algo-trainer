#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>a(n),prefix(n+1);for(auto &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)prefix[i+1]=prefix[i]+a[i];long long delta=0;
while(m--){int op;cin>>op;if(op==1){long long k;cin>>k;delta+=k;}
    else{int p=(int)(upper_bound(a.begin(),a.end(),-delta)-a.begin());cout<<prefix[n]-prefix[p]+(n-p)*delta<<'\n';}}
    return 0;
}
