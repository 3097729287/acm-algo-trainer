#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long m,k;cin>>n>>m>>k;vector<pair<long long,long long>>cows(n);for(auto &[w,a]:cows) cin>>w>>a;
sort(cows.begin(),cows.end(),greater<pair<long long,long long>>());deque<pair<long long,long long>>towers;towers.push_back({LLONG_MAX/4,m});long long answer=0;
for(auto [w,count]:cows){long long remaining=count;while(remaining&&!towers.empty()&&towers.front().first>=w+k){long long used=min(remaining,towers.front().second);remaining-=used;towers.front().second-=used;if(towers.front().second==0) towers.pop_front();}long long used=count-remaining;if(used){towers.push_back({w,used});answer+=used;}}
cout<<answer<<'\n';
    return 0;
}
