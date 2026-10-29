#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a,b,x;cin>>a>>b>>x;if(x==a||x==b){cout<<"-1\n";return 0;}
int l=a,r=b,left=0;vector<bool>pending;vector<pair<int,int>>operations;
while(l<r){
    if(2*x==l+r){operations.push_back({left,left+r-l});pending.push_back(true);++left;++l;--r;}
    else if(2*x<l+r){pending.push_back(true);++left;x=2*x-l;++l;}
    else{pending.push_back(false);x=2*x-r;--r;}
}
for(int i=(int)pending.size()-1;i>=0;--i){if(pending[i]){operations.push_back({left-1,left});--left;}else operations.push_back({left,left+1});}
for(auto op:operations)cout<<op.first<<' '<<op.second<<'\n';
    return 0;
}
