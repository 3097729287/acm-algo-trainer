#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int l, m; cin >> l >> m;
vector<bool> removed(l+1,false);
while (m--) { int a,b; cin >> a >> b; for(int x=a;x<=b;++x) removed[x]=true; }
int answer=0; for(int x=0;x<=l;++x) answer += !removed[x];
cout << answer << '\n';
    return 0;
}
