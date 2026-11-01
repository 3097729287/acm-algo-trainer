#include <bits/stdc++.h>
using namespace std;
int score(char b,char a){if(b==a)return 0;return ((b=='R'&&a=='S')||(b=='S'&&a=='P')||(b=='P'&&a=='R'))?1:-1;}
bool ok(const string &bob,vector<int>&a,int at,int sum){if(at==(int)bob.size())return sum>=0;string moves="RSP";for(int i=0;i<3;i++){if(a[i]==0)continue;--a[i];bool good=ok(bob,a,at+1,sum+score(bob[at],moves[i]));++a[i];if(!good)return false;}return true;}
bool search(string &s,int n,vector<int>&a){if((int)s.size()==n)return ok(s,a,0,0);for(char c:string("RSP")){s+=c;if(search(s,n,a))return true;s.pop_back();}return false;}
int main(){int t;cin>>t;while(t--){vector<int>a(3);cin>>a[0]>>a[1]>>a[2];int n=a[0]+a[1]+a[2];string s;search(s,n,a);cout<<s<<'\n';}}
