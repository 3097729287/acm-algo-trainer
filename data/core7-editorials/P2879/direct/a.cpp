#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,highest,height,relations;cin>>n>>highest>>height>>relations;vector<int>difference(n+2);set<pair<int,int>>seen;
while(relations--){int l,r;cin>>l>>r;if(l>r)swap(l,r);
    if(seen.insert({l,r}).second&&l+1<r){--difference[l+1];++difference[r];}}
int change=0;for(int i=1;i<=n;++i){change+=difference[i];cout<<height+change<<'\n';}
    return 0;
}
