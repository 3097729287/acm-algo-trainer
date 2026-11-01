#include <bits/stdc++.h>
using namespace std;
int main(){int T;cin>>T;while(T--){int n;cin>>n;vector<int>a(n),p(n);for(int &x:a)cin>>x;iota(p.begin(),p.end(),1);long long ans=0;
do{int bad=0;for(int i=0;i<n;i++)bad+=p[i]>a[i];ans+=bad==2;}while(next_permutation(p.begin(),p.end()));cout<<ans<<'\n';}}
