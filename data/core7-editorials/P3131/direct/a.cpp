#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;int first[7];fill(first,first+7,-1);first[0]=0;int remainder=0,answer=0;
for(int i=1;i<=n;++i){int id;cin>>id;remainder=(remainder+id)%7;
    if(first[remainder]==-1)first[remainder]=i;else answer=max(answer,i-first[remainder]);}
cout<<answer<<'\n';
    return 0;
}
