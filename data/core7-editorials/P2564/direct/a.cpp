#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<pair<long long,int>>beads;beads.reserve(n);
for(int color=0;color<k;++color){int count;cin>>count;while(count--){long long position;cin>>position;beads.push_back({position,color});}}
sort(beads.begin(),beads.end());vector<int>count(k);int covered=0,left=0;long long answer=LLONG_MAX;
for(int right=0;right<n;++right){if(count[beads[right].second]++==0) ++covered;while(covered==k){answer=min(answer,beads[right].first-beads[left].first);if(--count[beads[left].second]==0) --covered;++left;}}
cout<<answer<<'\n';
    return 0;
}
