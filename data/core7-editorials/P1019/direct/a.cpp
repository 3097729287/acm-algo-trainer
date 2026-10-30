#include <bits/stdc++.h>
using namespace std;
int n,answer=0;vector<string>words;vector<vector<pair<int,int>>>edges;
vector<int>used,maximum_gain;vector<long long>power;
unordered_map<long long,int>memo;
int continuation(int last,long long code){
    long long key=code*n+last;auto at=memo.find(key);
    if(at!=memo.end())return at->second;
    int upper=0,best=0;for(int i=0;i<n;++i)upper+=(2-used[i])*maximum_gain[i];
    for(auto [gain,next]:edges[last])if(used[next]<2){
        // 去掉本次使用的乐观增长，再加上这条边的实际增长。
        if(gain+upper-maximum_gain[next]<=best)continue;
        ++used[next];best=max(best,gain+continuation(next,code+power[next]));--used[next];
        if(best==upper)break;
    }
    return memo[key]=best; // 此处缓存精确的后续增长，与此前的拼接长度无关。
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>n;words.resize(n);for(auto &word:words)cin>>word;char first;cin>>first;
edges.resize(n);used.assign(n,0);maximum_gain.assign(n,0);power.resize(n);long long value=1;
for(int i=0;i<n;++i){power[i]=value;value*=3;}
for(int i=0;i<n;++i)for(int j=0;j<n;++j){
    for(int overlap=1;overlap<(int)min(words[i].size(),words[j].size());++overlap)
        if(words[i].substr(words[i].size()-overlap)==words[j].substr(0,overlap)){
            int gain=(int)words[j].size()-overlap;edges[i].push_back({gain,j});maximum_gain[j]=max(maximum_gain[j],gain);break;
        }
}
for(auto &list:edges)sort(list.rbegin(),list.rend());
for(int i=0;i<n;++i)if(words[i][0]==first){used[i]=1;answer=max(answer,(int)words[i].size()+continuation(i,power[i]));used[i]=0;}
cout<<answer<<'\n';
    return 0;
}
