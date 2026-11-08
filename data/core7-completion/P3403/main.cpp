#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long h;
    array<int, 3> a;
    cin >> h >> a[0] >> a[1] >> a[2];
    sort(a.begin(), a.end());
    int x = a[0];
    vector<long long> d(x, -1);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[1 % x] = 1;
    q.push({1, 1 % x});
    while (!q.empty()) {
        auto [v, r] = q.top();
        q.pop();
        if (d[r] != v)
            continue;
        for (int step : {a[1], a[2]})
            if (h >= step && v <= h - step) {
                long long nd = v + step;
                int nr = (r + step) % x;
                if (d[nr] < 0 || nd < d[nr]) {
                    d[nr] = nd;
                    q.push({nd, nr});
                }
            }
    }
    long long ans = 0;
    for (long long v : d)
        if (v >= 0 && v <= h)
            ans += (h - v) / x + 1;
    cout << ans << '\n';

    return 0;
}
