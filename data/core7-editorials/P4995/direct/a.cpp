#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>h(n);for(auto &x:h)cin>>x;sort(h.begin(),h.end());
int l=0,r=n-1;long long last=0,answer=0;bool high=true;
while(l<=r){long long next=high?h[r--]:h[l++],difference=next-last;answer+=difference*difference;last=next;high=!high;}
cout<<answer<<'\n';
    return 0;
}
