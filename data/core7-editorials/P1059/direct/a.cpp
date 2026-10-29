#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;bool present[1001]={};while(n--){int x;cin>>x;present[x]=true;}
int count=0;for(int x=1;x<=1000;++x)count+=present[x];cout<<count<<'\n';
bool first=true;for(int x=1;x<=1000;++x)if(present[x]){if(!first)cout<<' ';cout<<x;first=false;}cout<<'\n';
    return 0;
}
