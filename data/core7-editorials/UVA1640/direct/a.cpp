#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
auto prefix=[&](long long n){
    array<long long,10>count={};if(n<=0) return count;
    for(long long place=1;place<=n;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        for(int d=1;d<=9;++d){count[d]+=high*place;if(current>d) count[d]+=place;else if(current==d) count[d]+=low+1;}
        if(high>0) count[0]+=(high-1)*place+(current==0?low+1:place);
    }
    return count;
};
long long a,b;
while(cin>>a>>b&&(a||b)){
    if(a>b) swap(a,b);auto low=prefix(a-1),high=prefix(b);
    for(int d=0;d<10;++d) cout<<(d?" ":"")<<high[d]-low[d];cout<<'\n';
}
    return 0;
}
