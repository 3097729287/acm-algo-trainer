#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,p; cin>>n>>m>>p;
vector<vector<int>> coin(n,vector<int>(m));
for(auto &row:coin) for(int &x:row) cin>>x;
vector<int> cost(n); for(int &x:cost) cin>>x;
vector<long long> prefix(n);
vector<deque<pair<int,long long>>> window(n);
long long best=0;
for(int t=1;t<=m;++t){
    int s=t-1; long long next=LLONG_MIN/4;
    for(int d=0;d<n;++d){
        int road=(d+s)%n;
        long long candidate=best-prefix[d]-cost[road];
        auto &q=window[d];
        while(!q.empty()&&q.back().second<=candidate) q.pop_back();
        q.push_back({s,candidate});
        while(q.front().first<t-p) q.pop_front();
        prefix[d]+=coin[road][s];
        next=max(next,prefix[d]+q.front().second);
    }
    best=next; // 全部路径都只读取同一个上一秒最优值。
}
cout<<best<<'\n';
    return 0;
}
