#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n);vector<uint64_t>b(n),delta;for(int &x:a)cin>>x;for(auto &x:b)cin>>x;sort(a.begin(),a.end());sort(b.begin(),b.end());
vector<int>waiting;int index=0;long long time=a[0];
while((int)delta.size()<n){
    if(waiting.empty()&&index<n)time=max(time,(long long)a[index]);
    while(index<n&&a[index]<=time)waiting.push_back(a[index++]);
    delta.push_back(time-waiting.back());waiting.pop_back();++time;
}
sort(delta.begin(),delta.end());uint64_t answer=0;
for(int i=0;i<n;++i)answer+=delta[n-1-i]*b[i];cout<<answer<<'\n';
    return 0;
}
