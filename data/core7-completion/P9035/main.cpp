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
    int V = 0;
    for (auto &[n, k] : queries) {
        cin >> n >> k;
        int h = (k + 1) / 2;
        V = max({V, n + h - 1, n + k - h - 1});
    }
    vector<int> f(V + 1, 1), inv(V + 1, 1);
    for (int i = 1; i <= V; i++)
        f[i] = 1LL * f[i - 1] * i % MOD;
    inv[V] = power(f[V], MOD - 2);
    for (int i = V; i >= 1; i--)
        inv[i - 1] = 1LL * inv[i] * i % MOD;
    auto C = [&](int n, int k) -> long long {
        if (n < k || k < 0)
            return 0;
        return 1LL * f[n] * inv[k] % MOD * inv[n - k] % MOD;
    };
    for (auto [n, k] : queries) {
        int h = (k + 1) / 2;
        cout << (C(n + h - 1, n) + C(n + k - h - 1, n)) % MOD << '\n';
    }

    return 0;
}
