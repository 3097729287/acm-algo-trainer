#include <bits/stdc++.h>
using namespace std;
int ones(unsigned long long x){int count=0;while(x){count+=x&1ULL;x>>=1;}return count;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
unsigned long long A,B;cin>>A>>B;int answer=ones(B);
for(int k=0;k<63;++k)if((B>>k)&1ULL){
    unsigned long long bit=1ULL<<k,low=bit-1,candidate=(B&~(low|bit))|low;
    if(candidate>=A)answer=max(answer,ones(candidate));
}cout<<answer<<'\n';
    return 0;
}
