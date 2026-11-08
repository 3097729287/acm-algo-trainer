#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    const int V = 200000;
    vector<int> spf(V + 1), primes;
    for (int i = 2; i <= V; i++) {
        if (!spf[i]) {
            spf[i] = i;
            primes.push_back(i);
        }
        for (int p : primes) {
            if (p > spf[i] || 1LL * i * p > V)
                break;
            spf[i * p] = p;
        }
    }
    vector<vector<int>> positions(V + 1);
    vector<int> a(n + 1);
    vector<long long> pref(n + 1, 1), invPref(n + 1, 1), inv(V + 1);
    inv[1] = 1;
    for (int i = 2; i <= V; i++)
        inv[i] = (MOD - MOD / i) * inv[MOD % i] % MOD;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        pref[i] = pref[i - 1] * a[i] % MOD;
        int x = a[i];
        while (x > 1) {
            int p = spf[x], pw = 1;
            while (x % p == 0) {
                x /= p;
                pw *= p;
                positions[pw].push_back(i);
            }
        }
    }
    invPref[n] = power(pref[n], MOD - 2);
    for (int i = n; i >= 1; i--)
        invPref[i - 1] = invPref[i] * a[i] % MOD;
    while (q--) {
        int l, r, x;
        cin >> l >> r >> x;
        long long ans = pref[r] * invPref[l - 1] % MOD * power(x, r - l + 1) % MOD;
        while (x > 1) {
            int p = spf[x], pw = 1;
            long long exponent = 0;
            while (x % p == 0) {
                x /= p;
                pw *= p;
                auto &v = positions[pw];
                exponent += upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l);
            }
            ans = ans * power(inv[p], exponent) % MOD;
        }
        cout << ans << '\n';
    }

    return 0;
}
