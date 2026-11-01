#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m,k;long long increment;cin>>n>>m>>k>>increment;vector<long long>a(n+1);for(int i=1;i<=n;++i) cin>>a[i];vector<pair<int,int>>intervals(m);for(auto &[l,r]:intervals) cin>>l>>r;sort(intervals.begin(),intervals.end());
auto feasible=[&](long long target){vector<int>expiration(n+2);priority_queue<int>ends;int next=0,active=0,used=0;for(int i=1;i<=n;++i){active+=expiration[i];while(next<m&&intervals[next].first<=i) ends.push(intervals[next++].second);long long shortage=target-a[i]-increment*active;if(shortage<=0) continue;long long need=(shortage+increment-1)/increment;if(used+need>k) return false;while(need--){while(!ends.empty()&&ends.top()<i) ends.pop();if(ends.empty()) return false;int r=ends.top();ends.pop();++active;++used;--expiration[r+1];}}return true;};
long long low=*min_element(a.begin()+1,a.end()),high=low+k*increment;while(low<high){long long middle=(low+high+1)/2;if(feasible(middle)) low=middle;else high=middle-1;}cout<<low<<'\n';}
    return 0;
}
