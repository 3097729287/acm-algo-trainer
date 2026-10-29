#include <bits/stdc++.h>
using namespace std;
using Big=array<int,500>;
Big multiply(const Big&a,const Big&b){
    Big c{};for(int i=0;i<500;++i)for(int j=0;i+j<500;++j)c[i+j]+=a[i]*b[j];
    for(int i=0;i<499;++i){c[i+1]+=c[i]/10;c[i]%=10;}c[499]%=10;return c;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int p;cin>>p;cout<<(long long)floor(p*log10l(2.0L))+1<<'\n';
Big result{},base{};result[0]=1;base[0]=2;
while(p){if(p&1)result=multiply(result,base);base=multiply(base,base);p>>=1;}
--result[0];for(int i=499;i>=0;--i){cout<<result[i];if(i%50==0)cout<<'\n';}
    return 0;
}
