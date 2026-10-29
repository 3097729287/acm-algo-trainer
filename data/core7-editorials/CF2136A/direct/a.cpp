#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;
while(t--){int a,b,c,d;cin>>a>>b>>c>>d;
    bool first=max(a,b)<=2*(min(a,b)+1);
    int x=c-a,y=d-b;
    bool second=max(x,y)<=2*(min(x,y)+1);
    cout<<(first&&second?"YES":"NO")<<'\n';
}
    return 0;
}
