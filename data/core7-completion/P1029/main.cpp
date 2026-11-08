#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y;
    cin >> x >> y;
    if (y % x) {
        cout << 0 << '\n';
        return 0;
    }
    long long p = y / x, ans = 0;
    for (long long a = 1; a <= p / a; a++)
        if (p % a == 0 && gcd(a, p / a) == 1)
            ans += a == p / a ? 1 : 2;
    cout << ans << '\n';

    return 0;
}
