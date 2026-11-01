#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<int,int>>points(n);vector<int>ys;for(auto &[x,y]:points){cin>>x>>y;ys.push_back(y);}sort(points.begin(),points.end());sort(ys.begin(),ys.end());
int side=n+1;vector<int>prefix(side*side),rank(n);for(int i=0;i<n;++i){rank[i]=lower_bound(ys.begin(),ys.end(),points[i].second)-ys.begin()+1;prefix[(i+1)*side+rank[i]]=1;}
for(int x=1;x<=n;++x) for(int y=1;y<=n;++y) prefix[x*side+y]+=prefix[(x-1)*side+y]+prefix[x*side+y-1]-prefix[(x-1)*side+y-1];
auto count=[&](int left,int right,int low,int high){return prefix[right*side+high]-prefix[left*side+high]-prefix[right*side+low]+prefix[left*side+low];};
long long answer=1;for(int left=0;left<n;++left) for(int right=left;right<n;++right){int low=min(rank[left],rank[right]),high=max(rank[left],rank[right]);long long bottom=count(left,right+1,0,low),top=count(left,right+1,high-1,n);answer+=bottom*top;}
cout<<answer<<'\n';
    return 0;
}
