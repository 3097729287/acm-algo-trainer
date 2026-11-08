#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    vector<array<int, 3>> queries(tests);
    int limit = 0;
    for (auto &q : queries) {
        cin >> q[0] >> q[1] >> q[2];
        limit = max(limit, q[0]);
    }
    const long long mod = 998244353;
    vector<long long> fact(limit + 1, 1), inv(limit + 1, 1);
    for (int i = 1; i <= limit; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[limit] = power(fact[limit], mod - 2, mod);
    for (int i = limit; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int n, int k) {
        if (k < 0 || k > n)
            return 0LL;
        return fact[n] * inv[k] % mod * inv[n - k] % mod;
    };
    for (auto q : queries) {
        auto [m, a, b] = q;
        cout << choose(m - b, a) * choose(m - a, b) % mod << '\n';
    }

    return 0;
}
