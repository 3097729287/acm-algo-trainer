#include <bits/stdc++.h>
using namespace std;
int main(){int x;cin>>x;vector<int>d(x+1,x+1);d[0]=0;for(int i=1;i<=x;++i){d[i]=d[i-1]+1;if(i%2==0)d[i]=min(d[i],d[i/2]);}cout<<d[x]<<'\n';}
