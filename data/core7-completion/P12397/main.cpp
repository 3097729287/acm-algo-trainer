#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    long long k;
    cin >> tests >> k;
    auto digitSum = [](long long x) {
        int s = 0;
        for (; x; x /= 10)
            s += x % 10;
        return s;
    };
    vector<long long> contribution(172);
    for (int s = 1; s <= 171; s++) {
        long long value = s, left = k, total = 0;
        while (left && value >= 10) {
            total += value;
            value = digitSum(value);
            left--;
        }
        contribution[s] = total + value * left;
    }
    while (tests--) {
        long long m;
        cin >> m;
        if (!k) {
            cout << 1 << '\n';
            continue;
        }
        int answer = 0;
        for (int s = 1; s <= 171; s++)
            if (m > contribution[s]) {
                long long x = m - contribution[s];
                if (digitSum(x) == s)
                    answer++;
            }
        cout << answer << '\n';
    }

    return 0;
}
