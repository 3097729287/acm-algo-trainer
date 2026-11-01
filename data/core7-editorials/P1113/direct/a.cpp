#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<long long>finish(n+1);long long answer=0;
for(int i=0;i<n;++i){int u,duration;cin>>u>>duration;int v;long long wait=0;
    while(cin>>v&&v)wait=max(wait,finish[v]);
    finish[u]=wait+duration;answer=max(answer,finish[u]);
}cout<<answer<<'\n';
    return 0;
}
