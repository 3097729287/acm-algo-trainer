#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>cost(n),capacity(m);for(auto &x:cost) cin>>x;for(auto &x:capacity) cin>>x;
sort(cost.begin(),cost.end());sort(capacity.begin(),capacity.end(),greater<long long>());
long long answer=0;int first=0,lane=0;
while(first<m){if(lane==n){cout<<-1<<'\n';return 0;}int group=0;while(first+group<m&&group+1<=capacity[first+group]) ++group;answer+=group*cost[lane];first+=group;++lane;}
cout<<answer<<'\n';
    return 0;
}
