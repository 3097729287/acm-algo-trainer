#include <bits/stdc++.h>
using namespace std;
bool enough(const vector<long long>&a,long long small,long long large,long long height,long long target){
    long long total=0,full=0;vector<long long>remainders;
    for(long long x:a){long long need=max(0LL,target-x);total+=need;full+=need/height;if(need%height)remainders.push_back(need%height);}
    // 不浪费的整份收益最大；只有它们填完后才覆盖余数。
    if(full>=large)return total-large*height<=small;
    long long take=large-full;if(take>=(long long)remainders.size())return true;
    long long remaining=total-full*height;
    nth_element(remainders.begin(),remainders.begin()+take,remainders.end(),greater<long long>());
    for(long long i=0;i<take;++i)remaining-=remainders[i];return remaining<=small;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long m,k,h;cin>>n>>m>>k>>h;vector<long long>a(n);long long sum=0,lo=LLONG_MAX;
for(auto &x:a){cin>>x;sum+=x;lo=min(lo,x);}long long hi=(sum+m+k*h)/n;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;if(enough(a,m,k,h,mid))lo=mid;else hi=mid-1;}
cout<<lo<<'\n';
    return 0;
}
