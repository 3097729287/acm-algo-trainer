#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>difference(n+2);
for(int i=0,l,r;i<m;++i){cin>>l>>r;++difference[l];--difference[r+1];}
int count=0;for(int day=1;day<=n;++day){count+=difference[day];if(count!=1){cout<<day<<' '<<count<<'\n';return 0;}}
cout<<"OK\n";
    return 0;
}
