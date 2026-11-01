#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const long long MOD=998244353;long long l,r;int k;cin>>l>>r>>k;array<int,1024>bits={};for(int s=1;s<1024;++s) bits[s]=bits[s>>1]+(s&1);
auto prefix=[&](long long x){
    if(x<=0) return 0LL;string digits=to_string(x);vector<array<long long,2>>count(1024),sum(1024);count[0][1]=1;
    for(char c:digits){
        vector<array<long long,2>>nextCount(1024),nextSum(1024);
        for(int mask=0;mask<1024;++mask) for(int tight=0;tight<2;++tight) if(count[mask][tight]||sum[mask][tight]){
            int limit=tight?c-'0':9;
            for(int d=0;d<=limit;++d){
                int next=mask==0&&d==0?0:mask|(1<<d);if(bits[next]>k) continue;int nt=tight&&d==limit;
                nextCount[next][nt]=(nextCount[next][nt]+count[mask][tight])%MOD;
                nextSum[next][nt]=(nextSum[next][nt]+10*sum[mask][tight]+d*count[mask][tight])%MOD;
            }
        }
        count.swap(nextCount);sum.swap(nextSum);
    }
    long long answer=0;for(auto value:sum) answer=(answer+value[0]+value[1])%MOD;return answer;
};
cout<<(prefix(r)-prefix(l-1)+MOD)%MOD<<'\n';
    return 0;
}
