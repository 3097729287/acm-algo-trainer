#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<long long>duration(n),start(n),finish(n),times={0};for(auto &x:duration) cin>>x;
priority_queue<long long,vector<long long>,greater<long long>>ready;
for(int i=0;i<k;++i){finish[i]=duration[i];ready.push(finish[i]);}
for(int i=k;i<n;++i){start[i]=ready.top();ready.pop();finish[i]=start[i]+duration[i];ready.push(finish[i]);}
long long when=ready.top();for(int i=0;i<n;++i){times.push_back(start[i]);times.push_back(finish[i]);}sort(times.begin(),times.end());times.erase(unique(times.begin(),times.end()),times.end());
auto index=[&](long long time){return int(lower_bound(times.begin(),times.end(),time)-times.begin());};
vector<vector<int>>previous(times.size());for(int i=0;i<n;++i) previous[index(finish[i])].push_back(index(start[i]));
vector<char>visited(times.size());vector<int>stack={index(when)};visited[stack.back()]=true;
while(!stack.empty()){int x=stack.back();stack.pop_back();for(int p:previous[x]) if(!visited[p]){visited[p]=true;stack.push_back(p);}}
cout<<when<<'\n';for(int i=0;i<k;++i) cout<<char('0'+visited[index(duration[i])]);cout<<'\n';
    return 0;
}
