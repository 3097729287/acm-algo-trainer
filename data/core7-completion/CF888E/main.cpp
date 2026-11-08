#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto enumerate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int z = s.size();
            for (int j = 0; j < z; j++)
                s.push_back((s[j] + a[i]) % mod);
        }
        return s;
    };
    auto l = enumerate(0, n / 2), r = enumerate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l) {
        auto it = upper_bound(r.begin(), r.end(), mod - 1 - x);
        if (it != r.begin())
            ans = max(ans, x + *prev(it));
    }
    cout << ans << '\n';

    return 0;
}
