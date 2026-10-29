#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){int n;cin>>n;set<int> seen;bool first=true;
    while(n--){int x;cin>>x;if(seen.insert(x).second){if(!first)cout<<' ';cout<<x;first=false;}}
    cout<<'\n';
}
    return 0;
}
