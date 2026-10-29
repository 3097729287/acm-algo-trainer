#include <bits/stdc++.h>
using namespace std;
int n,r;vector<int>path;
void dfs(int start){
    if((int)path.size()==r){for(int x:path)cout<<setw(3)<<x;cout<<'\n';return;}
    int need=r-path.size();
    for(int x=start;x<=n-need+1;++x){path.push_back(x);dfs(x+1);path.pop_back();}
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>n>>r;dfs(1);
    return 0;
}
