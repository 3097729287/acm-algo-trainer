#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; cin >> s; int count[26]={};for(char c:s)++count[c-'a'];
int low=s.size(), high=0;for(int c:count)if(c){low=min(low,c);high=max(high,c);}
int d=high-low;bool prime=d>=2;for(int x=2;x*x<=d;++x)if(d%x==0)prime=false;
if(prime)cout<<"Lucky Word\n"<<d<<'\n';else cout<<"No Answer\n0\n";
    return 0;
}
