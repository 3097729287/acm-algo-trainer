#include <bits/stdc++.h>
using namespace std;
int main() {
    int T; cin >> T;
    while (T--) {
        int n, x; cin >> n >> x;
        vector<long long> c(n);
        for (auto &v : c) cin >> v;
        long long ans = LLONG_MAX;
        for (int mask = 0; mask < (1 << n); ++mask) {
            int score = 0;
            long long cost = 0;
            bool ok = true;
            for (int i = 0; i < n; ++i) {
                if (mask >> i & 1) { --score; cost += c[i]; }
                else ++score;
                if (score > x) ok = false;
            }
            if (ok && score > 0) ans = min(ans, cost);
        }
        cout << (ans == LLONG_MAX ? -1 : ans) << '\n';
    }
}
