#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const int limit = 10000010;
    vector<int> least(limit + 1), primes;
    for (int i = 2; i <= limit; i++) {
        if (!least[i]) {
            least[i] = i;
            primes.push_back(i);
        }
        for (int p : primes) {
            if (p > least[i] || 1LL * i * p > limit)
                break;
            least[i * p] = p;
        }
    }
    int tests;
    cin >> tests;
    vector<int> stamp(limit + 1);
    for (int test = 1; test <= tests; test++) {
        int n;
        cin >> n;
        while (n--) {
            int x;
            cin >> x;
            while (x > 1) {
                int p = least[x];
                stamp[p] = test;
                while (x % p == 0)
                    x /= p;
            }
        }
        for (int p : primes)
            if (stamp[p] != test) {
                cout << p << '\n';
                break;
            }
    }

    return 0;
}
