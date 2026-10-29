#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<int,long long>>jobs(n);for(auto &job:jobs)cin>>job.first>>job.second;sort(jobs.begin(),jobs.end());
priority_queue<long long,vector<long long>,greater<long long>>chosen;long long answer=0;
for(auto job:jobs){chosen.push(job.second);answer+=job.second;
    if((long long)chosen.size()>job.first){answer-=chosen.top();chosen.pop();}
}cout<<answer<<'\n';
    return 0;
}
