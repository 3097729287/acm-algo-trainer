#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<long long>>bucket(n+1);
for(int i=0;i<n;++i){int deadline;long long profit;cin>>deadline>>profit;bucket[min(deadline,n)].push_back(profit);}
priority_queue<long long>available;long long answer=0;
for(int t=n;t>=1;--t){for(long long profit:bucket[t])available.push(profit);if(!available.empty()){answer+=available.top();available.pop();}}
cout<<answer<<'\n';
    return 0;
}
