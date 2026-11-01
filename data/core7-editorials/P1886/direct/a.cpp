#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<int>a(n);for(int &x:a) cin>>x;
for(int maximum=0;maximum<2;++maximum){deque<int>queue;bool first=true;
    for(int i=0;i<n;++i){while(!queue.empty()&&queue.front()<i-k+1) queue.pop_front();while(!queue.empty()&&(maximum?a[queue.back()]<=a[i]:a[queue.back()]>=a[i])) queue.pop_back();queue.push_back(i);if(i>=k-1){if(!first) cout<<' ';first=false;cout<<a[queue.front()];}}
    cout<<'\n';
}
    return 0;
}
