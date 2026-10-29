#include <bits/stdc++.h>
using namespace std;
struct DSU{
    vector<int>p,size;
    DSU(int n):p(n),size(n,1){iota(p.begin(),p.end(),0);}
    int find(int x){while(x!=p[x]){p[x]=p[p[x]];x=p[x];}return x;}
    void join(int a,int b){a=find(a);b=find(b);if(a==b)return;if(size[a]<size[b])swap(a,b);p[b]=a;size[a]+=size[b];}
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;DSU dsu(n);vector<int>u(m),v(m),f(m);bool ok=true;
for(int i=0;i<m;++i){cin>>u[i]>>v[i]>>f[i];--u[i];--v[i];if(f[i]>1)ok=false;if(f[i]==0)dsu.join(u[i],v[i]);}
for(int i=0;i<m;++i)if(f[i]==1&&dsu.find(u[i])==dsu.find(v[i]))ok=false;
if(!ok){cout<<"No\n";return 0;}cout<<"Yes\n";
for(int i=0;i<m;++i)cout<<(f[i]==0?1:0)<<(i+1==m?'\n':' ');
    return 0;
}
