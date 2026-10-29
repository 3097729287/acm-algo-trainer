#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;bool first=true;
for(int power=n;power>=0;--power){int coefficient;cin>>coefficient;if(coefficient==0)continue;
    if(coefficient<0)cout<<'-';else if(!first)cout<<'+';
    int value=abs(coefficient);
    if(power==0||value!=1)cout<<value;
    if(power>0){cout<<'x';if(power>1)cout<<'^'<<power;}
    first=false;
}
if(first)cout<<0;cout<<'\n';
    return 0;
}
