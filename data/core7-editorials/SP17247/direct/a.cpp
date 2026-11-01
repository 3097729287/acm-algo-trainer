#include <bits/stdc++.h>
using namespace std;
long long prefix(long long n){
    if(n<=0) return 0;long long answer=0;
    for(long long place=1;;place*=10){
        long long high=n/place/10,current=n/place%10,low=n%place;
        answer+=high*45*place+current*(current-1)/2*place+current*(low+1);
        if(place>n/10) break;
    }
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){long long a,b;cin>>a>>b;cout<<prefix(b)-prefix(a-1)<<'\n';}
    return 0;
}
