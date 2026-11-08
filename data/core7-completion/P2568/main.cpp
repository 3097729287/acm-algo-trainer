#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> phi(n + 1);
    vector<bool> composite(n + 1);
    vector<int> primes;
    phi[1] = 1;
    for (int i = 2; i <= n; i++) {
        if (!composite[i]) {
            primes.push_back(i);
            phi[i] = i - 1;
        }
        for (int p : primes) {
            long long x = 1LL * i * p;
            if (x > n)
                break;
            composite[x] = true;
            if (i % p == 0) {
                phi[x] = phi[i] * p;
                break;
            }
            phi[x] = phi[i] * (p - 1);
        }
    }
    for (int i = 1; i <= n; i++)
        phi[i] += phi[i - 1];
    long long ans = 0;
    for (int p : primes)
        ans += 2 * phi[n / p] - 1;
    cout << ans << '\n';

    return 0;
}
