#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>bits;while(n){bits.push_back(n%2);n/=2;}
cout<<"1\n";for(int i=(int)bits.size()-2;i>=0;--i){cout<<"dup\nadd\n";if(bits[i])cout<<"1\nadd\n";}
    return 0;
}
