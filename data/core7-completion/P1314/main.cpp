#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    long long target;
    cin >> n >> m >> target;
    vector<int> w(n + 1), v(n + 1);
    int maximum = 0;
    for (int i = 1; i <= n; i++) {
        cin >> w[i] >> v[i];
        maximum = max(maximum, w[i]);
    }
    vector<pair<int, int>> ranges(m);
    for (auto &[l, r] : ranges)
        cin >> l >> r;
    vector<long long> cnt(n + 1), sum(n + 1);
    auto value = [&](int W) {
        for (int i = 1; i <= n; i++) {
            bool take = w[i] >= W;
            cnt[i] = cnt[i - 1] + take;
            sum[i] = sum[i - 1] + (take ? v[i] : 0);
        }
        __int128 y = 0;
        for (auto [l, r] : ranges)
            y += (__int128)(cnt[r] - cnt[l - 1]) * (sum[r] - sum[l - 1]);
        return y;
    };
    long long ans = target;
    int lo = 0, hi = maximum + 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        __int128 y = value(mid), diff = y - target;
        if (diff < 0)
            diff = -diff;
        if (diff < ans)
            ans = diff;
        if (y > target)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    cout << ans << '\n';

    return 0;
}
