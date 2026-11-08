#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    long long x = n;
    vector<long long> primes;
    for (long long p = 2; p <= x / p; p++)
        if (x % p == 0) {
            primes.push_back(p);
            while (x % p == 0)
                x /= p;
        }
    if (x > 1)
        primes.push_back(x);
    auto phi = [&](long long x) {
        long long r = x;
        for (long long p : primes)
            if (x % p == 0)
                r = r / p * (p - 1);
        return r;
    };
    long long ans = 0;
    for (long long d = 1; d <= n / d; d++)
        if (n % d == 0) {
            ans += d * phi(n / d);
            if (d != n / d)
                ans += (n / d) * phi(d);
        }
    cout << ans << '\n';

    return 0;
}
