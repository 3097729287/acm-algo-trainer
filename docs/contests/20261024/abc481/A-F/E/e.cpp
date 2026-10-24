#include <bits/stdc++.h>
using namespace std;
struct Point { long long x, y; };
int half(Point p) {
    return (p.y > 0 || (p.y == 0 && p.x > 0)) ? 0 : 1;
}
long long cross(Point a, Point b) {
    return a.x * b.y - a.y * b.x;
}
bool angle_less(Point a, Point b) {
    if (half(a) != half(b)) return half(a) < half(b);
    return cross(a, b) > 0;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<Point> p(n);
        for (Point &v : p) cin >> v.x >> v.y;
        sort(p.begin(), p.end(), angle_less);
        for (int i = 0; i < n; ++i) p.push_back(p[i]);
        int answer = 1, right = 0;
        for (int left = 0; left < n; ++left) {
            right = max(right, left + 1);
            // 从起点逆时针转动不足半圈，叉积严格为正。
            while (right < left + n && cross(p[left], p[right]) > 0) ++right;
            answer = max(answer, right - left);
        }
        cout << answer << '\n';
    }
}
