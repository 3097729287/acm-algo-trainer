#include <bits/stdc++.h>
using namespace std;
string plus_decimal(const string &a,const string &b){
    int i=(int)a.size()-1,j=(int)b.size()-1,carry=0;string result;
    while(i>=0||j>=0||carry){
        int value=carry;if(i>=0)value+=a[i--]-'0';if(j>=0)value+=b[j--]-'0';
        result.push_back(char('0'+value%10));carry=value/10;
    }
    reverse(result.begin(),result.end());return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m,n;cin>>m>>n;string a="1",b="1";
for(int d=2;d<=n-m;++d){string next=plus_decimal(a,b);a=b;b=next;}
cout<<b<<'\n';
    return 0;
}
