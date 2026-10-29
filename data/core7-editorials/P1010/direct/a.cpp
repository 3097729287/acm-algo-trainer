#include <bits/stdc++.h>
using namespace std;
void print_number(int x){
    bool first=true;
    for(int k=14;k>=0;--k)if((x>>k)&1){
        if(!first)cout<<'+';first=false;
        if(k==0)cout<<"2(0)";
        else if(k==1)cout<<'2';
        else{cout<<"2(";print_number(k);cout<<')';}
    }
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;print_number(n);cout<<'\n';
    return 0;
}
