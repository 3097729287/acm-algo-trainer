#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        unsigned long long k, n;
        cin >> k >> n;
        bool ok;
        if (n == 0)
            ok = k >= 1;
        else {
            unsigned long long ones = __builtin_popcountll(n - 1), d = min(k, (k + ones) / 2);
            if (d >= 61)
                ok = true;
            else {
                unsigned long long value = 1ULL << d;
                ok = value >= n && value - n >= k - d;
            }
        }
        cout << (ok ? "Yes" : "No") << '\n';
    }

    return 0;
}
