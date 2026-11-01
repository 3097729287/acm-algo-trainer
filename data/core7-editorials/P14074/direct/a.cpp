#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long l,r;cin>>l>>r;
auto prefix=[&](long long x){
    if(x<0) return 0LL;long long count[2][2]={},sum[2][2]={};count[1][0]=1;
    for(int pos=30;pos>=0;--pos){
        long long nextCount[2][2]={},nextSum[2][2]={};int bit=(x>>pos)&1;
        for(int tight=0;tight<2;++tight) for(int parity=0;parity<2;++parity){
            int limit=tight?bit:1;
            for(int d=0;d<=limit;++d){
                int nt=tight&&d==limit,np=parity^d;
                nextCount[nt][np]+=count[tight][parity];nextSum[nt][np]+=2*sum[tight][parity]+d*count[tight][parity];
            }
        }
        for(int t=0;t<2;++t) for(int p=0;p<2;++p){count[t][p]=nextCount[t][p];sum[t][p]=nextSum[t][p];}
    }
    return sum[0][1]+sum[1][1];
};
cout<<prefix(r)-prefix(l-1)<<'\n';
    return 0;
}
