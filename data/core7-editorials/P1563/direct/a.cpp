#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>face(n);vector<string>name(n);
for(int i=0;i<n;++i)cin>>face[i]>>name[i];int pos=0;
while(m--){int direction,steps;cin>>direction>>steps;
    if(face[pos]==direction)pos=(pos-steps+n)%n;else pos=(pos+steps)%n;
}cout<<name[pos]<<'\n';
    return 0;
}
