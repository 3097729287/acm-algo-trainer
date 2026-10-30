#include <bits/stdc++.h>
using namespace std;
bool possible(const vector<long long>&value,const vector<long long>&cost,int chosen,long long p,long long q){
    // 固定阈值后，选转换得分最高的恰好 m 项。
    vector<long long>score(value.size());for(size_t i=0;i<value.size();++i)score[i]=q*value[i]-p*cost[i];
    sort(score.rbegin(),score.rend());long long sum=0;for(int i=0;i<chosen;++i)sum+=score[i];return sum>=0;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<long long>value(n),cost(n);for(auto &x:value)cin>>x;for(auto &x:cost)cin>>x;
long long lo=0,hi=1000000;
while(lo<hi){long long mid=(lo+hi+1)/2;if(possible(value,cost,m,mid,1000))lo=mid;else hi=mid-1;}
// 精确比较半个千分位，达到半点时进一。
if(possible(value,cost,m,2*lo+1,2000))++lo;
cout<<lo/1000<<'.'<<setw(3)<<setfill('0')<<lo%1000<<'\n';
    return 0;
}
