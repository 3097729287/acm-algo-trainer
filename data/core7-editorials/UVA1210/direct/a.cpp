#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const int LIMIT=10000;vector<bool>prime(LIMIT+1,true);prime[0]=prime[1]=false;
for(int p=2;p*p<=LIMIT;++p)if(prime[p])for(int multiple=p*p;multiple<=LIMIT;multiple+=p)prime[multiple]=false;
vector<int>primes,ways(LIMIT+1);for(int x=2;x<=LIMIT;++x)if(prime[x])primes.push_back(x);
for(int l=0;l<(int)primes.size();++l){int sum=0;for(int r=l;r<(int)primes.size();++r){sum+=primes[r];if(sum>LIMIT)break;++ways[sum];}}
int n;while(cin>>n&&n!=0)cout<<ways[n]<<'\n';
    return 0;
}
