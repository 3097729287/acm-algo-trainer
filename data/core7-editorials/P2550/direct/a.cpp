#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n; bool win[34]={}; int count[8]={};
for(int i=0;i<7;++i){int x;cin>>x;win[x]=true;}
while(n--){int hits=0;for(int i=0;i<7;++i){int x;cin>>x;hits+=win[x];}++count[hits];}
for(int i=7;i>=1;--i) cout << count[i] << (i==1?'\n':' ');
    return 0;
}
