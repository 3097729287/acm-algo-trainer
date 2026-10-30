#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,b;cin>>n>>b;deque<long long>finish;vector<long long>answer;
for(int i=0;i<n;++i){long long t,d;cin>>t>>d;while(!finish.empty()&&finish.front()<=t)finish.pop_front();
    // b 是等待位；另有一项可以正在执行。
    if((int)finish.size()>b){answer.push_back(-1);continue;}
    long long end=max(t,finish.empty()?t:finish.back())+d;finish.push_back(end);answer.push_back(end);
}
for(int i=0;i<n;++i)cout<<answer[i]<<(i+1==n?'\n':' ');
    return 0;
}
