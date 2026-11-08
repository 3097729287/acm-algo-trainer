#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a, b;
    cin >> a >> b;
    auto solve = [](long long n) {
        long long ans = 0;
        for (long long j = 1; j <= n; j++) {
            long long q = n / j;
            long long value = j * q * (q - 1) / 2 + q * (n - q * j + 1);
            ans += (j % 2 ? -value : value);
        }
        return ans;
    };
    cout << solve(b) - solve(a - 1) << '\n';

    return 0;
}
