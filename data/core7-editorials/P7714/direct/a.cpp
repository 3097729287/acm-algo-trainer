#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){
    int n;cin>>n;int maximum=0,previous=0,answer=0;
    for(int i=1;i<=n;++i){int x;cin>>x;maximum=max(maximum,x);
        if(maximum==i){int length=i-previous;if(length>1)answer+=length;previous=i;}}
    cout<<answer<<'\n';
}
    return 0;
}
