#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long m;cin>>n>>m;long long sum=0,minimum=LLONG_MAX,maximum=LLONG_MIN;
for(int i=0;i<n;++i){long long x;cin>>x;sum+=x;minimum=min(minimum,x);maximum=max(maximum,x);}
// 最小值保持不变，其余项的最高值受原最大值与平均值共同限制。
long long retained_total=sum-minimum+m,highest=max(maximum,(retained_total+n-2)/(n-1));
cout<<retained_total-highest<<'\n';
    return 0;
}
