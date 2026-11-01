#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string n;cin>>n;long long choose[51][51]={};choose[0][0]=1;
for(int i=1;i<=50;++i) for(int j=0;j<=i;++j) choose[i][j]=(j?choose[i-1][j-1]:0)+choose[i-1][j];
array<int,10>count={};for(char c:n) ++count[c-'0'];
auto ways=[&](const array<int,10>&remaining){long long result=1;int used=0;for(int c:remaining){result*=choose[used+c][c];used+=c;}return result;};
long long answer=0;
for(int removed=1;removed<=count[0];++removed){
    auto rest=count;rest[0]-=removed;
    for(int first=1;first<=9;++first) if(rest[first]){--rest[first];answer+=ways(rest);++rest[first];}
}
for(int pos=0;pos<int(n.size());++pos){
    int current=n[pos]-'0';for(int d=(pos==0?1:0);d<current;++d) if(count[d]){--count[d];answer+=ways(count);++count[d];}
    --count[current];
}
cout<<answer<<'\n';
    return 0;
}
