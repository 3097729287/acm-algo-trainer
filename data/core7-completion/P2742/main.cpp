#include <bits/stdc++.h>
using namespace std;

struct Point {
    double x, y;
};
double cross(Point a, Point b, Point c) {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<Point> a(n);
    for (auto &v : a)
        cin >> v.x >> v.y;
    sort(a.begin(), a.end(), [](Point a, Point b) { return tie(a.x, a.y) < tie(b.x, b.y); });
    a.erase(unique(a.begin(), a.end(), [](Point a, Point b) { return a.x == b.x && a.y == b.y; }),
            a.end());
    vector<Point> h;
    for (auto p : a) {
        while (h.size() >= 2 && cross(h[h.size() - 2], h.back(), p) <= 0)
            h.pop_back();
        h.push_back(p);
    }
    int lower = h.size();
    for (int i = (int)a.size() - 2; i >= 0; i--) {
        auto p = a[i];
        while ((int)h.size() > lower && cross(h[h.size() - 2], h.back(), p) <= 0)
            h.pop_back();
        h.push_back(p);
    }
    if (h.size() > 1)
        h.pop_back();
    double ans = 0;
    for (int i = 0; i < (int)h.size(); i++) {
        auto p = h[i], q = h[(i + 1) % h.size()];
        ans += hypot(p.x - q.x, p.y - q.y);
    }
    cout << fixed << setprecision(2) << ans << '\n';

    return 0;
}
