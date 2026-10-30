#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>a(n),cuts(m);for(int &x:a)cin>>x;for(int &x:cuts)cin>>x;sort(cuts.begin(),cuts.end());
// 只在一个非空保留段的开头计数。
int answer=0;bool inside=false;
for(int x:a){auto found=lower_bound(cuts.begin(),cuts.end(),x);bool removed=found!=cuts.end()&&*found==x;
    if(!removed&&!inside)++answer;inside=!removed;
}
cout<<answer<<'\n';
    return 0;
}
