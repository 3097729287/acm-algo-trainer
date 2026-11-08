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

    int T;
    cin >> T;
    vector<pair<int, int>> queries(T);
    int N = 0;
    for (auto &[n, m] : queries) {
        cin >> n >> m;
        N = max(N, n);
    }
    vector<long long> f(N + 1, 1), inv(N + 1, 1), d(N + 1);
    d[0] = 1;
    for (int i = 1; i <= N; i++)
        f[i] = f[i - 1] * i % MOD;
    for (int i = 2; i <= N; i++)
        d[i] = (i - 1) * (d[i - 1] + d[i - 2]) % MOD;
    inv[N] = power(f[N], MOD - 2);
    for (int i = N; i >= 1; i--)
        inv[i - 1] = inv[i] * i % MOD;
    for (auto [n, m] : queries)
        cout << (m > n ? 0 : f[n] * inv[m] % MOD * inv[n - m] % MOD * d[n - m] % MOD) << '\n';

    return 0;
}
