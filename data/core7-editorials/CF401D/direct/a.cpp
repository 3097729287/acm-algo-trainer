#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string n;int modulus;cin>>n>>modulus;array<int,10>count={},stride={},radix={};for(char c:n) ++count[c-'0'];
int states=1;for(int d=0;d<10;++d){stride[d]=states;radix[d]=count[d]+1;states*=radix[d];}
vector<long long>dp(states*modulus);dp[0]=1;
for(int code=0;code<states;++code){
    for(int d=0;d<10;++d){
        int used=code/stride[d]%radix[d];if(used==count[d]||(code==0&&d==0)) continue;
        int next=code+stride[d];
        for(int r=0;r<modulus;++r) dp[next*modulus+(r*10+d)%modulus]+=dp[code*modulus+r];
    }
}
cout<<dp[(states-1)*modulus]<<'\n';
    return 0;
}
