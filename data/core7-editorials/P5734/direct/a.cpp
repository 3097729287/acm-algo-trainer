#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int q;string s;cin>>q>>s;
while(q--){int type;cin>>type;
    if(type==1){string t;cin>>t;s+=t;cout<<s<<'\n';}
    else if(type==2){int start,len;cin>>start>>len;s=s.substr(start,len);cout<<s<<'\n';}
    else if(type==3){int pos;string t;cin>>pos>>t;s.insert(pos,t);cout<<s<<'\n';}
    else {string t;cin>>t;size_t pos=s.find(t);if(pos==string::npos)cout<<-1<<'\n';else cout<<pos<<'\n';}
}
    return 0;
}
