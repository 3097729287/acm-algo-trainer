#include <bits/stdc++.h>
using namespace std;
string turn(string s,bool fractional){
    reverse(s.begin(),s.end());
    if(fractional){while(s.size()>1 && s.back()=='0')s.pop_back();}
    else {size_t p=s.find_first_not_of('0');s=p==string::npos?"0":s.substr(p);}
    return s;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s;cin>>s;
size_t pos=s.find_first_of("./%");
if(pos==string::npos) cout<<turn(s,false);
else if(s[pos]=='%') cout<<turn(s.substr(0,pos),false)<<'%';
else cout<<turn(s.substr(0,pos),false)<<s[pos]<<turn(s.substr(pos+1),s[pos]=='.');
cout<<'\n';
    return 0;
}
