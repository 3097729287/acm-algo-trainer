#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m1, m2;
    cin >> n >> m1 >> m2;
    vector<pair<long long, long long>> factors;
    long long x = m1;
    for (long long p = 2; p <= x / p; p++)
        if (x % p == 0) {
            long long e = 0;
            while (x % p == 0) {
                x /= p;
                e++;
            }
            factors.push_back({p, e * m2});
        }
    if (x > 1)
        factors.push_back({x, m2});
    long long answer = LLONG_MAX;
    while (n--) {
        long long s;
        cin >> s;
        long long time = 0;
        bool ok = true;
        for (auto [p, need] : factors) {
            long long c = 0;
            while (s % p == 0) {
                s /= p;
                c++;
            }
            if (c == 0 && need) {
                ok = false;
                break;
            }
            if (need)
                time = max(time, (need + c - 1) / c);
        }
        if (ok)
            answer = min(answer, time);
    }
    cout << (answer == LLONG_MAX ? -1 : answer) << '\n';

    return 0;
}
