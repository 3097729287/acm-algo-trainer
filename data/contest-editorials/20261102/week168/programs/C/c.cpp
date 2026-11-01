#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long m, total = 0, prefix = 0;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a) { cin >> x; total += x; }
    int ans = 0;
    for (long long x : a) {
        // 此时 prefix 是当前位置之前的和；两边都包含当前的 x。
        long long suffix = total - prefix;
        prefix += x;
        if ((prefix - suffix) % m == 0) ++ans;
    }
    cout << ans << '\n';
}
