#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;string s;cin>>n>>s;vector<int>first(2*n+1,-1);int sum=0,answer=0;first[n]=0;
for(int i=1;i<=n;++i){
    sum+=s[i-1]=='1'?1:-1;int at=sum+n;
    if(first[at]==-1)first[at]=i;else answer=max(answer,i-first[at]);
}
cout<<answer<<'\n';
    return 0;
}
