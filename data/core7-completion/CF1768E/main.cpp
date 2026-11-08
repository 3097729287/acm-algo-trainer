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

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> fact(3 * n + 1, 1), inv(3 * n + 1, 1);
    for (int i = 1; i <= 3 * n; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[3 * n] = power(fact[3 * n], mod - 2, mod);
    for (int i = 3 * n; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int a, int b) { return fact[a] * inv[b] % mod * inv[a - b] % mod; };
    long long one = (2 * fact[2 * n] - fact[n] + mod) % mod, sum = 0;
    for (int x = 0; x <= n; x++) {
        long long value = choose(n, x);
        sum = (sum + value * value % mod * choose(n + x, x)) % mod;
    }
    long long intersection = fact[n] * fact[n] % mod * fact[n] % mod * sum % mod;
    long long two =
        (2 * choose(2 * n, n) % mod * fact[n] % mod * fact[2 * n] % mod - intersection + mod) % mod;
    cout << (3 * fact[3 * n] % mod - 1 - one - two + 3 * mod) % mod << '\n';

    return 0;
}
