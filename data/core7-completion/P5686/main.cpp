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

    int n;
    cin >> n;
    vector<long long> A(n + 1);
    for (int i = 1; i <= n; i++) {
        long long x;
        cin >> x;
        A[i] = (A[i - 1] + x) % MOD;
    }
    long long B = 0, sumA = 0, sumB = 0, sumAB = 0, ans = 0;
    for (int r = 1; r <= n; r++) {
        long long x;
        cin >> x;
        B = (B + x) % MOD;
        long long term = (r * A[r] % MOD * B - A[r] * sumB % MOD - B * sumA % MOD + sumAB) % MOD;
        ans = (ans + term + 2 * MOD) % MOD;
        sumA = (sumA + A[r]) % MOD;
        sumB = (sumB + B) % MOD;
        sumAB = (sumAB + A[r] * B) % MOD;
    }
    cout << ans << '\n';

    return 0;
}
