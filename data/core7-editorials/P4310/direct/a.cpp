#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;int best[64]={},answer=0;for(int i=0;i<n;++i){long long value;cin>>value;unsigned long long bits=value;int length=1;
    for(int b=0;b<64;++b)if(bits&(1ULL<<b))length=max(length,best[b]+1);
    for(int b=0;b<64;++b)if(bits&(1ULL<<b))best[b]=max(best[b],length);answer=max(answer,length);
}cout<<answer<<'\n';
    return 0;
}
