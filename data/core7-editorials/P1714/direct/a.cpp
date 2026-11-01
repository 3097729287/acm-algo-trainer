#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>prefix(n+1);deque<int>queue;queue.push_back(0);long long answer=LLONG_MIN;
for(int i=1;i<=n;++i){int x;cin>>x;prefix[i]=prefix[i-1]+x;while(queue.front()<i-m) queue.pop_front();answer=max(answer,prefix[i]-prefix[queue.front()]);while(!queue.empty()&&prefix[queue.back()]>=prefix[i]) queue.pop_back();queue.push_back(i);}
cout<<answer<<'\n';
    return 0;
}
