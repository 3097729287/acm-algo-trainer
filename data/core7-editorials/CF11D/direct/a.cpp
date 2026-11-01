#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>adjacent(n);
for(int i=0,u,v;i<m;++i){cin>>u>>v;--u;--v;adjacent[u]|=1<<v;adjacent[v]|=1<<u;}
int states=1<<n;vector<int>index(states);vector<unsigned char>size(states);
for(int i=0;i<n;++i) index[1<<i]=i;
for(int mask=1;mask<states;++mask) size[mask]=size[mask&(mask-1)]+1;
vector<long long>dp(size_t(states)*n);for(int i=0;i<n;++i) dp[size_t(1<<i)*n+i]=1;
long long directedCycles=0;
for(int mask=1;mask<states;++mask){
    int first=index[mask&-mask],greater=~((1<<(first+1))-1);
    for(int lastBits=mask;lastBits;lastBits&=lastBits-1){
        int last=index[lastBits&-lastBits];long long ways=dp[size_t(mask)*n+last];if(!ways) continue;
        if(size[mask]>=3&&(adjacent[last]>>first&1)) directedCycles+=ways;
        int candidates=adjacent[last]&~mask&greater;
        while(candidates){int bit=candidates&-candidates;candidates^=bit;int next=index[bit];dp[size_t(mask|bit)*n+next]+=ways;}
    }
}
cout<<directedCycles/2<<'\n';
    return 0;
}
