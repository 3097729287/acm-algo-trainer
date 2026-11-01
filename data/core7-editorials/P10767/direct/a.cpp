#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,queries;cin>>n>>queries;int total=1<<n;
vector<int>rule(total);for(int u=1;u<total;++u) cin>>rule[u];
vector<int>low(2*total,1),high(2*total,1),size(2*total,1);
for(int u=total-1;u>=1;--u){
    int l=2*u,r=l+1;size[u]=size[l]+size[r];
    if(rule[u]==1){low[u]=low[l]+low[r];high[u]=max(high[l]+size[r],high[r]+size[l]);}
    else{low[u]=min(low[l],low[r]);high[u]=high[l]+high[r]-1;}
}
vector<int>leftBound(n+1,1),rightBound(n+1,total);
for(int height=1;height<=n;++height){
    leftBound[height]=total;rightBound[height]=0;
    for(int u=total>>height;u<(total>>(height-1));++u){
        leftBound[height]=min(leftBound[height],low[u]);
        rightBound[height]=max(rightBound[height],total-size[u]+high[u]);
    }
}
while(queries--){int a,b;cin>>a>>b;int height=b-1;cout<<(leftBound[height]<=a&&a<=rightBound[height]?"Yes":"No")<<'\n';}
    return 0;
}
