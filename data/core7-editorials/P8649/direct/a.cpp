#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<long long>count(k);count[0]=1;int remainder=0;long long answer=0;
for(int i=0;i<n;++i){int x;cin>>x;remainder=(remainder+x)%k;answer+=count[remainder];++count[remainder];}
cout<<answer<<'\n';
    return 0;
}
