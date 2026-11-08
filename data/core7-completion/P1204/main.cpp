#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<pair<int, int>> a(n);
    for (auto &[l, r] : a)
        cin >> l >> r;
    sort(a.begin(), a.end());
    int l = a[0].first, r = a[0].second, busy = 0, idle = 0;
    for (int i = 1; i < n; i++) {
        if (a[i].first <= r)
            r = max(r, a[i].second);
        else {
            busy = max(busy, r - l);
            idle = max(idle, a[i].first - r);
            tie(l, r) = a[i];
        }
    }
    busy = max(busy, r - l);
    cout << busy << ' ' << idle << '\n';

    return 0;
}
