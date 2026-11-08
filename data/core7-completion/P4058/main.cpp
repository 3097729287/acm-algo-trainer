#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long need, limit;
    cin >> n >> need >> limit;
    vector<long long> h(n), growth(n);
    for (auto &x : h)
        cin >> x;
    for (auto &x : growth)
        cin >> x;
    auto ok = [&](long long day) {
        __int128 sum = 0;
        for (int i = 0; i < n; i++) {
            __int128 height = h[i] + (__int128)growth[i] * day;
            if (height >= limit)
                sum += height;
            if (sum >= need)
                return true;
        }
        return false;
    };
    long long l = 0, r = 1;
    while (!ok(r))
        r *= 2;
    while (l < r) {
        long long mid = l + (r - l) / 2;
        if (ok(mid))
            r = mid;
        else
            l = mid + 1;
    }
    cout << l << '\n';

    return 0;
}
