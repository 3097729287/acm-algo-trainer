#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<long long,long long>>swaps(n);vector<long long>x;for(auto &[a,b]:swaps){cin>>a>>b;x.push_back(a);x.push_back(b);}
sort(x.begin(),x.end());x.erase(unique(x.begin(),x.end()),x.end());int c=x.size();vector<int>p(c);iota(p.begin(),p.end(),0);
for(auto [a,b]:swaps){int u=lower_bound(x.begin(),x.end(),a)-x.begin(),v=lower_bound(x.begin(),x.end(),b)-x.begin();swap(p[u],p[v]);}
vector<int>bit(c+1);auto sum=[&](int i){int s=0;for(;i;i-=i&-i)s+=bit[i];return s;};long long answer=0;
for(int i=0;i<c;++i){answer+=i-sum(p[i]+1);for(int j=p[i]+1;j<=c;j+=j&-j)++bit[j];
    answer+=llabs(x[i]-x[p[i]])-abs(i-p[i]);
}cout<<answer<<'\n';
    return 0;
}
