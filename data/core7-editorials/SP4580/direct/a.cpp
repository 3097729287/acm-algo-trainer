#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>values(n);for(auto &x:values)cin>>x;vector<long long>left;left.reserve(n*n*n);
for(long long a:values)for(long long b:values)for(long long c:values)left.push_back(a*b+c);
sort(left.begin(),left.end());long long answer=0;
for(long long d:values)if(d!=0)for(long long e:values)for(long long f:values){
    long long target=d*(e+f);
    // 相同值的三元组各算一次，不把 left 去重。
    answer+=upper_bound(left.begin(),left.end(),target)-lower_bound(left.begin(),left.end(),target);
}
cout<<answer<<'\n';
    return 0;
}
