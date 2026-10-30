#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>count(1<<20);count[0]=1;int prefix=0;long long answer=0;
for(int i=0;i<n;++i){int x;cin>>x;prefix^=x;answer+=count[prefix];++count[prefix];}
cout<<answer<<'\n';
    return 0;
}
