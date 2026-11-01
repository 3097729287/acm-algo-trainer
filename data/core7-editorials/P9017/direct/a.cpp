#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests,n;cin>>tests>>n;int states=1<<n,full=states-1;
auto rotate=[&](int mask){return ((mask<<1)&full)|(mask>>(n-1));};
auto parse=[&](const string &s){int mask=0;for(int i=0;i<n;++i) if(s[i]=='1') mask|=1<<i;return mask;};
vector<int>representative(states,-1);
for(int mask=0;mask<states;++mask) if(representative[mask]<0){
    int current=mask;while(representative[current]<0){representative[current]=mask;current=rotate(current);}
}
vector<vector<unsigned char>>can(3*n+1,vector<unsigned char>(states));can[0][representative[0]]=true;int pad=0;
for(int steps=1;steps<=3*n;++steps){
    pad^=1<<((steps-1)%n);
    for(int mask=0;mask<states;++mask) if(can[steps-1][representative[mask]]) can[steps][representative[mask^pad]]=true;
}
while(tests--){
    string a,b;cin>>a>>b;int lights=parse(a),switches=parse(b),baseline=0,answer=-1;
    for(int steps=0;steps<=3*n;++steps){
        if(can[steps][representative[lights^baseline]]){answer=steps;break;}
        baseline^=switches;switches=rotate(switches);
    }
    cout<<answer<<'\n';
}
    return 0;
}
