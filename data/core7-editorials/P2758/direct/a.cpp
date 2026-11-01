#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string a,b;cin>>a>>b;int n=a.size(),m=b.size();vector<int>prev(m+1),current(m+1);iota(prev.begin(),prev.end(),0);
for(int i=1;i<=n;++i){current[0]=i;for(int j=1;j<=m;++j)current[j]=min({prev[j]+1,current[j-1]+1,prev[j-1]+(a[i-1]!=b[j-1])});prev.swap(current);}
cout<<prev[m]<<'\n';
    return 0;
}
