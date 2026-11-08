#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto generate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int size = s.size();
            for (int j = 0; j < size; j++)
                if (a[i] <= m - s[j])
                    s.push_back(s[j] + a[i]);
        }
        return s;
    };
    auto l = generate(0, n / 2), r = generate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l)
        ans += upper_bound(r.begin(), r.end(), m - x) - r.begin();
    cout << ans << '\n';

    return 0;
}
