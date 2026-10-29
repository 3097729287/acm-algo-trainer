#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n);iota(a.begin(),a.end(),1);
do{for(int x:a)cout<<setw(5)<<x;cout<<'\n';}while(next_permutation(a.begin(),a.end()));
    return 0;
}
