#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,test=0;while(cin>>n){
    vector<long long>a(n);for(auto &x:a)cin>>x;long long answer=0;
    for(int l=0;l<n;++l){long long product=1;for(int r=l;r<n;++r){product*=a[r];answer=max(answer,product);}}
    cout<<"Case #"<<++test<<": The maximum product is "<<answer<<".\n\n";
}
    return 0;
}
