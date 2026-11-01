#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;while(n--){long long x;cin>>x;int count=0;for(long long d=1;d<=x/d;++d)if(x%d==0)count+=(d==x/d?1:2);cout<<(count==3?"YES":"NO")<<'\n';}}
