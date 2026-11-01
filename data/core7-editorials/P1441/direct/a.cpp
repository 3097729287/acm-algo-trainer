#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>weight(n);for(int &x:weight) cin>>x;int answer=0;
auto evaluate=[&](int removed){
    bitset<2001>possible;possible[0]=1;
    for(int i=0;i<n;++i) if(!(removed>>i&1)) possible|=possible<<weight[i];
    answer=max(answer,int(possible.count())-1);
};
function<void(int,int,int)> choose=[&](int start,int left,int removed){
    if(left==0){evaluate(removed);return;}
    for(int i=start;i<=n-left;++i) choose(i+1,left-1,removed|(1<<i));
};
choose(0,m,0);cout<<answer<<'\n';
    return 0;
}
