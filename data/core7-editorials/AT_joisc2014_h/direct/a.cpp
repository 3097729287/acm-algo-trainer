#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;string s;cin>>n>>s;map<pair<int,int>,int>first;first[{0,0}]=0;
int jo=0,ji=0,answer=0;
for(int i=1;i<=n;++i){
    if(s[i-1]=='J'){++jo;++ji;}else if(s[i-1]=='O')--jo;else --ji;
    pair<int,int>state={jo,ji};auto found=first.find(state);
    if(found==first.end())first[state]=i;else answer=max(answer,i-found->second);
}
cout<<answer<<'\n';
    return 0;
}
