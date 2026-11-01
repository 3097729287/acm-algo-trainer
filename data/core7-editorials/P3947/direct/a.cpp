#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long target,deadline;cin>>n>>target>>deadline;
vector<string>name(n);vector<int>duration(n),open(n),nameRank(n);long long totalTime=0;
for(int i=0;i<n;++i){cin>>name[i]>>duration[i]>>open[i];totalTime+=duration[i];if(i) nameRank[i]=nameRank[i-1]+(name[i]!=name[i-1]);}
if(totalTime>deadline){cout<<"No Answer\n";return 0;}
int states=1<<n,full=states-1;vector<int>elapsed(states);vector<unsigned char>count(states);vector<vector<int>>layer(n+1);
layer[0].push_back(0);
for(int mask=1;mask<states;++mask){
    int first=0;while(!(mask>>first&1)) ++first;int rest=mask^(1<<first);
    elapsed[mask]=elapsed[rest]+duration[first];count[mask]=count[rest]+1;layer[count[mask]].push_back(mask);
}
vector<long long>dp(states);
for(int mask=full-1;mask>=0;--mask) for(int j=0;j<n;++j) if(!(mask>>j&1)){
    long long gain=max(0LL,1LL*open[j]-elapsed[mask]-duration[j]);dp[mask]=max(dp[mask],gain+dp[mask|(1<<j)]);
}
if(dp[0]<target){cout<<"No Answer\n";return 0;}
vector<int>rank(states);vector<unsigned char>choice(states,255);
for(int used=n-1;used>=0;--used){
    vector<pair<unsigned long long,int>>keys;keys.reserve(layer[used].size());
    for(int mask:layer[used]){
        unsigned long long best=ULLONG_MAX;int selectedName=-1;
        for(int j=0;j<n;++j) if(!(mask>>j&1)){
            if(selectedName>=0&&nameRank[j]>selectedName) break;
            int next=mask|(1<<j);long long gain=max(0LL,1LL*open[j]-elapsed[mask]-duration[j]);
            if(gain+dp[next]!=dp[mask]) continue;
            unsigned long long key=(static_cast<unsigned long long>(nameRank[j])<<32)|static_cast<unsigned int>(rank[next]);
            if(key<best){best=key;choice[mask]=j;selectedName=nameRank[j];}
        }
        keys.push_back({best,mask});
    }
    sort(keys.begin(),keys.end());int current=0;
    for(size_t i=0;i<keys.size();++i){if(i&&keys[i].first!=keys[i-1].first) ++current;rank[keys[i].second]=current;}
}
cout<<dp[0]<<'\n';int mask=0;
while(mask!=full){int j=choice[mask];cout<<name[j]<<'\n';mask|=1<<j;}
    return 0;
}
