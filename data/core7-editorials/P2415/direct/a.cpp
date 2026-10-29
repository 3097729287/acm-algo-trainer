#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long x,sum=0;int n=0;while(cin>>x){sum+=x;++n;}
cout<<sum*(1LL<<(n-1))<<'\n';
    return 0;
}
