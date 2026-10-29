#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;while(cin>>n){vector<long long>a(n);for(auto &x:a)cin>>x;vector<bool>seen(n);
    for(int i=1;i<n;++i){long long d=abs(a[i]-a[i-1]);if(d>0&&d<n)seen[d]=true;}
    bool ok=true;for(int d=1;d<n;++d)if(!seen[d])ok=false;
    cout<<(ok?"Jolly":"Not jolly")<<'\n';
}
    return 0;
}
