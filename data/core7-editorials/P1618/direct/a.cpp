#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long A,B,C;cin>>A>>B>>C;bool found=false;
if(A>0)for(int x=100;x<=999;++x){
    if(x*B%A||x*C%A)continue;long long y=x*B/A,z=x*C/A;
    if(y<100||y>999||z<100||z>999)continue;
    bool used[10]={},ok=true;
    for(int value:{x,(int)y,(int)z})while(value){int d=value%10;value/=10;if(d==0||used[d])ok=false;used[d]=true;}
    if(ok){cout<<x<<' '<<y<<' '<<z<<'\n';found=true;}
}
if(!found)cout<<"No!!!\n";
    return 0;
}
