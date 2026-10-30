#include <bits/stdc++.h>
using namespace std;
bool finishes(const vector<long long>&duration,int capacity,long long limit){
    priority_queue<long long,vector<long long>,greater<long long>>ends;
    for(int i=0;i<capacity;++i)ends.push(0);
    // 堆顶是最早空位的完成时刻，而非单头表演时长。
    for(long long d:duration){long long finish=ends.top()+d;ends.pop();if(finish>limit)return false;ends.push(finish);}
    return true;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long limit;cin>>n>>limit;vector<long long>duration(n);for(auto &x:duration)cin>>x;int lo=1,hi=n;
while(lo<hi){int mid=(lo+hi)/2;if(finishes(duration,mid,limit))hi=mid;else lo=mid+1;}
cout<<lo<<'\n';
    return 0;
}
