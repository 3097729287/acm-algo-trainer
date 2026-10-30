#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,operations;long long modulus,minimum,maximum;cin>>n>>operations>>modulus>>minimum>>maximum;
vector<long long>difference(n+2);
while(operations--){char type;int l,r;cin>>type>>l>>r;
    if(type=='A'){long long x;cin>>x;difference[l]+=x;difference[r+1]-=x;}
    else{long long value=0;int answer=0;
        for(int i=1;i<=r;++i){value+=difference[i];if(i>=l){long long rem=(value%modulus)*i%modulus;answer+=minimum<=rem&&rem<=maximum;}}
        cout<<answer<<'\n';
    }
}
vector<int>prefix(n+1);long long value=0;
for(int i=1;i<=n;++i){value+=difference[i];long long rem=(value%modulus)*i%modulus;prefix[i]=prefix[i-1]+(minimum<=rem&&rem<=maximum);}
int final_queries;cin>>final_queries;while(final_queries--){int l,r;cin>>l>>r;cout<<prefix[r]-prefix[l-1]<<'\n';}
    return 0;
}
