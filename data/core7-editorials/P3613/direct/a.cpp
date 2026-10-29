#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,q;cin>>n>>q;map<pair<int,int>,int> item;
while(q--){int type,i,j;cin>>type>>i>>j;pair<int,int> key={i,j};
    if(type==1){int k;cin>>k;item[key]=k;}
    else {auto it=item.find(key);cout<<(it==item.end()?0:it->second)<<'\n';}
}
    return 0;
}
