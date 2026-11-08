#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> x(n), y(n), r(n);
    for (auto &v : x)
        cin >> v;
    for (auto &v : y)
        cin >> v;
    for (auto &v : r)
        cin >> v;
    long long x1, y1, x2, y2;
    cin >> x1 >> y1 >> x2 >> y2;
    int ans = 0;
    for (int i = 0; i < n; i++) {
        bool a = (x1 - x[i]) * (x1 - x[i]) + (y1 - y[i]) * (y1 - y[i]) < r[i] * r[i];
        bool b = (x2 - x[i]) * (x2 - x[i]) + (y2 - y[i]) * (y2 - y[i]) < r[i] * r[i];
        ans += a != b;
    }
    cout << ans << '\n';

    return 0;
}
