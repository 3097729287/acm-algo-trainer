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

    int n, k;
    cin >> n >> k;
    const long long mod = 998244353;
    if (k == 0) {
        cout << 1 << '\n';
        return 0;
    }
    int m = n - k;
    vector<long long> fact(m + 1, 1), inv(m + 1, 1);
    for (int i = 1; i <= m; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[m] = power(fact[m], mod - 2, mod);
    for (int i = m; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    long long ans = 0;
    for (int i = 0; i <= m; i++) {
        long long term = power(i, n, mod) * inv[i] % mod * inv[m - i] % mod;
        if ((m - i) & 1)
            ans = (ans - term + mod) % mod;
        else
            ans = (ans + term) % mod;
    }
    cout << ans << '\n';

    return 0;
}
