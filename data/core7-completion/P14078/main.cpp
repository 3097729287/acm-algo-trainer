#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<pair<long long, long long>> points;
    for (int i = 0; i < n; i++) {
        long long x, t;
        cin >> x >> t;
        if (x >= 0 && t >= x)
            points.push_back({x, t - x});
    }
    sort(points.begin(), points.end());
    vector<long long> tails;
    for (auto [x, y] : points) {
        auto it = upper_bound(tails.begin(), tails.end(), y);
        if (it == tails.end())
            tails.push_back(y);
        else
            *it = y;
    }
    cout << tails.size() << '\n';

    return 0;
}
