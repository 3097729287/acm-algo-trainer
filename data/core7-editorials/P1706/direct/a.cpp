#include <bits/stdc++.h>
using namespace std;
int n;bool used[10]={};vector<int>path;
void dfs(){
    if((int)path.size()==n){for(int x:path)cout<<setw(5)<<x;cout<<'\n';return;}
    for(int x=1;x<=n;++x)if(!used[x]){
        used[x]=true;path.push_back(x);dfs();path.pop_back();used[x]=false;
    }
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>n;dfs();
    return 0;
}
