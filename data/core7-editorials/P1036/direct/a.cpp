#include <bits/stdc++.h>
using namespace std;
int n,k,answer=0;vector<int>a;
bool prime(int x){if(x<2)return false;for(int d=2;1LL*d*d<=x;++d)if(x%d==0)return false;return true;}
void dfs(int start,int chosen,int sum){
    if(chosen==k){answer+=prime(sum);return;}
    int need=k-chosen;
    for(int i=start;i<=n-need;++i)dfs(i+1,chosen+1,sum+a[i]);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>n>>k;a.resize(n);for(int &x:a)cin>>x;dfs(0,0,0);cout<<answer<<'\n';
    return 0;
}
