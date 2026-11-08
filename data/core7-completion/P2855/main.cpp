#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int length, n, m;
    cin >> length >> n >> m;
    vector<int> a(n + 1);
    for (int i = 0; i < n; i++)
        cin >> a[i];
    sort(a.begin(), a.begin() + n);
    a[n] = length;
    auto ok = [&](int gap) {
        int removed = 0, last = 0;
        for (int x : a)
            if (x - last < gap)
                removed++;
            else
                last = x;
        return removed <= m;
    };
    int l = 0, r = length;
    while (l < r) {
        int mid = l + (r - l + 1) / 2;
        if (ok(mid))
            l = mid;
        else
            r = mid - 1;
    }
    cout << l << '\n';

    return 0;
}
