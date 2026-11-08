#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<bool> composite(n + 1);
    vector<int> primes;
    for (int i = 2; i <= n; i++) {
        if (!composite[i])
            primes.push_back(i);
        for (int p : primes) {
            long long x = 1LL * i * p;
            if (x > n)
                break;
            composite[x] = 1;
            if (i % p == 0)
                break;
        }
    }
    while (q--) {
        int k;
        cin >> k;
        cout << primes[k - 1] << '\n';
    }

    return 0;
}
