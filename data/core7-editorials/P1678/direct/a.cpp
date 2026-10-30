#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m,n;cin>>m>>n;vector<long long>schools(m);for(auto &x:schools)cin>>x;sort(schools.begin(),schools.end());long long answer=0;
// 二分位置及前驱是两侧各自最近的学校。
while(n--){long long x;cin>>x;int p=(int)(lower_bound(schools.begin(),schools.end(),x)-schools.begin());long long best=LLONG_MAX;
    if(p<m)best=min(best,schools[p]-x);if(p>0)best=min(best,x-schools[p-1]);answer+=best;
}
cout<<answer<<'\n';
    return 0;
}
