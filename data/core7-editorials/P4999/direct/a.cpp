#include <bits/stdc++.h>
using namespace std;
const long long MOD=1000000007;
long long prefix(long long n){
    if(n<=0) return 0;long long answer=0;
    for(long long place=1;;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        long long full=(high%MOD)*45%MOD*(place%MOD)%MOD;
        long long partial=current*(current-1)/2*(place%MOD)%MOD;
        long long tail=current*((low+1)%MOD)%MOD;
        answer=(answer+full+partial+tail)%MOD;if(place>n/10) break;
    }
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){long long l,r;cin>>l>>r;cout<<(prefix(r)-prefix(l-1)+MOD)%MOD<<'\n';}
    return 0;
}
