#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long b;cin>>n>>b;vector<int>h(n);for(int &x:h)cin>>x;sort(h.begin(),h.end(),greater<int>());
long long sum=0;for(int i=0;i<n;++i){sum+=h[i];if(sum>=b){cout<<i+1<<'\n';break;}}
    return 0;
}
