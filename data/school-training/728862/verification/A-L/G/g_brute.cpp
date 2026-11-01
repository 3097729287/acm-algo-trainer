#include <bits/stdc++.h>
using namespace std;
int main(){string s,ans;cin>>s;for(unsigned char ch:s){char c=char(tolower(ch));if(string("aoyeui").find(c)==string::npos)ans+=string(".")+c;}cout<<ans<<'\n';}
