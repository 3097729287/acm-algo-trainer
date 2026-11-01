#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
vector<int>coin(4);for(int &c:coin) cin>>c;int queries;cin>>queries;
vector<array<int,5>>data(queries);int maximum=0;for(auto &q:data){for(int &x:q) cin>>x;maximum=max(maximum,q[4]);}
vector<long long>ways(maximum+1);ways[0]=1;
for(int c:coin) for(int sum=c;sum<=maximum;++sum) ways[sum]+=ways[sum-c];
for(auto q:data){
    long long answer=0;
    for(int mask=0;mask<16;++mask){
        long long remaining=q[4];int selected=0;
        for(int i=0;i<4;++i) if(mask>>i&1){remaining-=1LL*(q[i]+1)*coin[i];++selected;}
        if(remaining>=0){if(selected%2) answer-=ways[remaining];else answer+=ways[remaining];}
    }
    cout<<answer<<'\n';
}
    return 0;
}
