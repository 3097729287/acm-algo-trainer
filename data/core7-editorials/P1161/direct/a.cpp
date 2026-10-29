#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n;
vector<bool> on(2000001,false);
while (n--) {
    string a; int t; cin >> a >> t; size_t dot=a.find('.');
    long long scaled=stoll(a.substr(0,dot))*1000000+stoll(a.substr(dot+1));
    for(int j=1;j<=t;++j) { int x=scaled*j/1000000; on[x]=!on[x]; }
}
for(int x=1;x<(int)on.size();++x) if(on[x]) { cout << x << '\n'; break; }
    return 0;
}
