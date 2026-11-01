#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;deque<pair<int,int>>queue;
for(int i=1;i<=n;++i){int x;cin>>x;while(!queue.empty()&&queue.front().second<i-m) queue.pop_front();cout<<(queue.empty()?0:queue.front().first)<<'\n';while(!queue.empty()&&queue.back().first>=x) queue.pop_back();queue.push_back({x,i});}
    return 0;
}
