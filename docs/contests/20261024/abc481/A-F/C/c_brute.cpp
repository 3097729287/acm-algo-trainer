#include <bits/stdc++.h>
using namespace std;
int main(){int q;cin>>q;vector<string>a;while(q--){string s;cin>>s;int k=0;while(k<(int)a.size()&&a[k]!=s)k++;if(k==(int)a.size())a.push_back(s);cout<<k+1<<'\n';}}
