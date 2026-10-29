#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;map<int,int> position;for(int i=1;i<=n;++i){int x;cin>>x;position[x]=i;}
int q;cin>>q;while(q--){int x;cin>>x;auto it=position.find(x);cout<<(it==position.end()?0:it->second)<<'\n';}
    return 0;
}
