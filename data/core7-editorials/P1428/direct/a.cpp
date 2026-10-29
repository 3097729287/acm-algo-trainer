#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n; vector<int> a(n); for(int &x:a) cin >> x;
for(int i=0;i<n;++i) {
    int count=0; for(int j=0;j<i;++j) if(a[j]<a[i]) ++count;
    cout << count << (i+1==n?'\n':' ');
}
    return 0;
}
