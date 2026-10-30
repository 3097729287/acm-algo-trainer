#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<long long,long long>>jobs(n);for(auto &job:jobs){cin>>job.second>>job.first;}sort(jobs.begin(),jobs.end());
// 每个截止前缀都对开工时间提出一个上限。
long long elapsed=0,latest=LLONG_MAX;
for(auto job:jobs){elapsed+=job.second;latest=min(latest,job.first-elapsed);}
cout<<(latest<0?-1:latest)<<'\n';
    return 0;
}
