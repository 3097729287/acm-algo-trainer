#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,r,k;cin>>n>>m>>r>>k;vector<int>a(n),b(m);
for(int i=1;i<=n;++i)a[i-1]=min({i,r,n-i+1,n-r+1});
for(int j=1;j<=m;++j)b[j-1]=min({j,r,m-j+1,m-r+1});
sort(a.rbegin(),a.rend());sort(b.rbegin(),b.rend());
using State=tuple<long long,int,int>;priority_queue<State>pq;
for(int i=0;i<n;++i)pq.push({1LL*a[i]*b[0],i,0});
// 每次只推进刚弹出的那一行乘积列表。
long long sum=0;for(int take=0;take<k;++take){auto [value,i,j]=pq.top();pq.pop();sum+=value;
    if(j+1<m)pq.push({1LL*a[i]*b[j+1],i,j+1});
}long long positions=1LL*(n-r+1)*(m-r+1);cout<<fixed<<setprecision(18)<<(long double)sum/positions<<'\n';
    return 0;
}
