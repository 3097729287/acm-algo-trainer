#include <bits/stdc++.h>
using namespace std;
struct BIT{
    int n;vector<long long>tree;
    BIT(int size):n(size),tree(size+1){}
    void add(int i,long long value){for(;i<=n;i+=i&-i)tree[i]+=value;}
    long long sum(int i)const{long long result=0;for(;i>0;i-=i&-i)result+=tree[i];return result;}
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<int,int>>cows(n);
for(auto &cow:cows)cin>>cow.first>>cow.second;
sort(cows.begin(),cows.end());BIT counts(20000),positions(20000);
long long processed=0,total_x=0,answer=0;
for(auto cow:cows){
    long long v=cow.first,x=cow.second;
    long long left_count=counts.sum((int)x),left_sum=positions.sum((int)x);
    long long distance=x*left_count-left_sum+(total_x-left_sum)-x*(processed-left_count);
    answer+=v*distance; // 此时 v 不小于此前任意奶牛的听力
    counts.add((int)x,1);positions.add((int)x,x);++processed;total_x+=x;
}
cout<<answer<<'\n';
    return 0;
}
