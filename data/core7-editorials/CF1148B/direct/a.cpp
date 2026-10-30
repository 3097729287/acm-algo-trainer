#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,k;long long ta,tb;cin>>n>>m>>ta>>tb>>k;vector<long long>a(n),b(m);for(auto &x:a)cin>>x;for(auto &x:b)cin>>x;
if(k>=n||k>=m){cout<<-1<<'\n';return 0;}long long answer=0;
// x 个取消名额给第一程，其余给中转后最早可接的航班。
for(int x=0;x<=k;++x){int first=(int)(lower_bound(b.begin(),b.end(),a[x]+ta)-b.begin());int selected=first+k-x;
    if(selected>=m){cout<<-1<<'\n';return 0;}answer=max(answer,b[selected]+tb);
}
cout<<answer<<'\n';
    return 0;
}
