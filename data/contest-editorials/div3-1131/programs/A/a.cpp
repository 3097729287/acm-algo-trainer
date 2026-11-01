#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        string p, q;
        cin >> n >> m >> p >> q;
        int count[26] = {};
        for (char c : p) ++count[c - 'a'];
        for (char c : q) --count[c - 'a'];
        // 再扣掉目标，所有差值为零才表示分母清空、分子恰好剩 six。
        for (char c : string("six")) --count[c - 'a'];
        bool ok = true;
        for (int value : count) if (value != 0) ok = false;
        cout << (ok ? "YES" : "NO") << '\n';
    }
}
