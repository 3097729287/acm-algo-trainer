#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;while(cin>>n&&n){array<int,100>count={};for(int i=0,age;i<n;++i){cin>>age;++count[age];}bool first=true;for(int age=1;age<100;++age) for(int c=0;c<count[age];++c){if(!first) cout<<' ';first=false;cout<<age;}cout<<'\n';}
    return 0;
}
