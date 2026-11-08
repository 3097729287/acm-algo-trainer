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

    long long m, n;
    cin >> m >> n;
    const long long mod = 100003;
    cout << (power(m % mod, n, mod) - (m % mod) * power((m - 1) % mod, n - 1, mod) % mod + mod) %
                mod
         << '\n';

    return 0;
}
