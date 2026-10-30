#include <bits/stdc++.h>
using namespace std;
string normalize(const string&s){size_t i=0;while(i+1<s.size()&&s[i]=='0')++i;return s.substr(i);}
string multiply(const string&a,long long factor){
    if(factor==0)return "0";string result;long long carry=0;
    for(int i=(int)a.size()-1;i>=0;--i){long long value=(a[i]-'0')*factor+carry;result.push_back(char('0'+value%10));carry=value/10;}
    while(carry){result.push_back(char('0'+carry%10));carry/=10;}
    reverse(result.begin(),result.end());return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string n,m;cin>>n>>m;n=normalize(n);m=normalize(m);long long lo=0,hi=1;
// 被除数很长，但商有 13! 这个可用 64 位整数保存的上限。
for(int i=2;i<=13;++i)hi*=i;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;string product=multiply(m,mid);
    bool fits=product.size()<n.size()||(product.size()==n.size()&&product<=n);
    if(fits)lo=mid;else hi=mid-1;
}
cout<<lo<<'\n';
    return 0;
}
