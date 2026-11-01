#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,q;cin>>n>>q;const long long bound=1000000000000000000LL;vector<int>parent(n+1);vector<long long>l(n+1),r(n+1),delta(n+1),offset(n+1),low(n+1),high(n+1);vector<char>valid(n+1);
for(int i=2;i<=n;++i) cin>>parent[i]>>l[i]>>r[i];for(int i=1;i<=n;++i){char op;long long a;cin>>op>>a;delta[i]=op=='+'?a:-a;}
valid[1]=true;low[1]=-bound;high[1]=bound;offset[1]=delta[1];vector<long long>starts={-bound},ends={bound};
for(int i=2;i<=n;++i){int p=parent[i];if(!valid[p]) continue;low[i]=max(low[p],l[i]-offset[p]);high[i]=min(high[p],r[i]-offset[p]);if(low[i]>high[i]) continue;valid[i]=true;offset[i]=offset[p]+delta[i];starts.push_back(low[i]);ends.push_back(high[i]);}
sort(starts.begin(),starts.end());sort(ends.begin(),ends.end());while(q--){long long x;cin>>x;cout<<(upper_bound(starts.begin(),starts.end(),x)-starts.begin())-(lower_bound(ends.begin(),ends.end(),x)-ends.begin())<<'\n';}
    return 0;
}
