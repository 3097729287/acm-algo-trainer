#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> a(n);
        for (auto &v : a) cin >> v;
        sort(a.begin(), a.end());
        long long median = a[n / 2], cost = 0;
        // 中位数两侧的距离之和等于按每个相邻差付出的最小锁定成本。
        for (long long v : a) cost += (v >= median ? v - median : median - v);
        cout << cost << ' ' << a.back() - a.front() << '\n';
    }
}
