#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;deque<pair<long long,int>>queue;
for(int i=0;i<n;++i){long long x;cin>>x;while(!queue.empty()&&queue.front().second<i-m+1) queue.pop_front();while(!queue.empty()&&queue.back().first>=x) queue.pop_back();queue.push_back({x,i});if(i>=m-1) cout<<queue.front().first<<'\n';}
    return 0;
}
