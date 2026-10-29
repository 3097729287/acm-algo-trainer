#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long a,b,p;cin>>a>>b>>p;long long base=a%p,e=b,result=1;
while(e>0){
    if(e&1)result=result*base%p; // 当前二进制位为一才选择该幂
    base=base*base%p;e>>=1;
}
cout<<a<<'^'<<b<<" mod "<<p<<'='<<result<<'\n';
    return 0;
}
