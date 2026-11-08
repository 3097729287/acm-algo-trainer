#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long P = 998244353;
    auto powmod = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long factorial = 1, denominator = 1;
    for (int i = 1; i <= 2 * n; i++) {
        factorial = factorial * i % P;
        if (i <= n + 1)
            denominator = denominator * i % P;
    }
    cout << factorial * powmod(denominator, P - 2) % P * powmod(2, n) % P << '\n';

    return 0;
}
