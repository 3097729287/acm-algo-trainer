#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y;
    cin >> x >> y;
    auto solve = [](long long n) {
        __int128 ans = 0;
        for (long long l = 1, r; l <= n; l = r + 1) {
            long long q = n / l;
            r = n / q;
            ans += (__int128)(l + r) * (r - l + 1) / 2 * q;
        }
        return ans;
    };
    __int128 v = solve(y) - solve(x - 1);
    string s;
    do {
        s.push_back('0' + v % 10);
        v /= 10;
    } while (v);
    reverse(s.begin(), s.end());
    cout << s << '\n';

    return 0;
}
