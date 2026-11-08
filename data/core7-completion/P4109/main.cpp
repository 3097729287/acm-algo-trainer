#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        long long l, r;
        cin >> l >> r;
        int best = INT_MAX;
        long long answer = l;
        auto test = [&](long long p) {
            if (p < l || p > r)
                return;
            long long x = p;
            while (x % 10 == 0)
                x /= 10;
            int score = 2 * (int)to_string(x).size() - (x % 10 == 5);
            if (score < best || (score == best && p < answer)) {
                best = score;
                answer = p;
            }
        };
        for (long long power = 1; power <= r; power *= 10) {
            long long q = (l + power - 1) / power;
            test(q * power);
            long long five = q + (5 - q % 10 + 10) % 10;
            test(five * power);
        }
        cout << answer << '\n';
    }

    return 0;
}
