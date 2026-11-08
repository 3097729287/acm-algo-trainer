#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    const long long mod = 998244353, inv2 = (mod + 1) / 2;
    auto solve = [&](long long n) {
        long long ans = 0;
        for (long long power = 4, k = 1; power / 2 - 1 <= n; power *= 2, k++) {
            long long l = max(1LL, power / 2 - 1), r = min(n, power - 2);
            if (l <= r) {
                long long count = (r - l + 1) % mod,
                          sum = (l % mod + r % mod) % mod * count % mod * inv2 % mod;
                long long constant = (-power % mod + k + 2 + mod) % mod;
                ans = (ans + (k + 1) * sum + constant * count) % mod;
            }
        }
        return ans;
    };
    while (tests--) {
        long long l, r;
        cin >> l >> r;
        cout << (solve(r) - solve(l - 1) + mod) % mod << '\n';
    }

    return 0;
}
