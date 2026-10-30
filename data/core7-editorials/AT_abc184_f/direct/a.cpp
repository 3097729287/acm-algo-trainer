#include <bits/stdc++.h>
using namespace std;
vector<long long>subset_sums(const vector<long long>&a,int begin,int end,long long limit){
    vector<long long>sums={0};
    for(int i=begin;i<end;++i){size_t previous=sums.size();
        // 本轮只从旧和扩展，不能重复选当前元素。
        for(size_t j=0;j<previous;++j)if(sums[j]+a[i]<=limit)sums.push_back(sums[j]+a[i]);
    }
    return sums;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long limit;cin>>n>>limit;vector<long long>a(n);for(auto &x:a)cin>>x;
auto left=subset_sums(a,0,n/2,limit),right=subset_sums(a,n/2,n,limit);sort(right.begin(),right.end());long long answer=0;
for(long long x:left){auto at=upper_bound(right.begin(),right.end(),limit-x);--at;answer=max(answer,x+*at);}
cout<<answer<<'\n';
    return 0;
}
