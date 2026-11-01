#include <bits/stdc++.h>
using namespace std;
int n,m,k;vector<long long>a,b;vector<int>c,d;long long ans;
void dfs(int i,int j,int last,long long sum){if(i+j==k){ans=max(ans,sum);return;}
if(i<n&&(last!=0||c[i-1]==0))dfs(i+1,j,0,sum+a[i]);
if(j<m&&(last!=1||d[j-1]==0))dfs(i,j+1,1,sum+b[j]);}
int main(){int T;cin>>T;while(T--){cin>>n>>m>>k;a.resize(n);b.resize(m);c.resize(n);d.resize(m);
for(int i=0;i<n;i++){cin>>a[i]>>c[i];}for(int i=0;i<m;i++){cin>>b[i]>>d[i];}ans=LLONG_MIN;dfs(0,0,2,0);
if(ans==LLONG_MIN)cout<<"IMPOSSIBLE\n";else cout<<ans<<'\n';}}
