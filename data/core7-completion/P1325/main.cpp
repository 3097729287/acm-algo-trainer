#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    double d;
    cin >> n >> d;
    vector<pair<double, double>> intervals;
    bool possible = true;
    for (int i = 0; i < n; i++) {
        double x, y;
        cin >> x >> y;
        if (abs(y) > d) {
            possible = false;
            continue;
        }
        double radius = sqrt(max(0.0, d * d - y * y));
        intervals.push_back({x - radius, x + radius});
    }
    if (!possible) {
        cout << -1 << '\n';
        return 0;
    }
    sort(intervals.begin(), intervals.end(), [](auto a, auto b) { return a.second < b.second; });
    int ans = 0;
    double last = -numeric_limits<double>::infinity();
    for (auto [l, r] : intervals)
        if (last < l) {
            last = r;
            ans++;
        }
    cout << ans << '\n';

    return 0;
}
