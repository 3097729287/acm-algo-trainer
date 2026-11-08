## UVA1303 Wall

原题：[UVA1303](https://www.luogu.com.cn/problem/UVA1303)

### 思路

先求城堡顶点凸包的周长，再加上安全距离 L 的一整圈圆周长 2πL。凸包每条边平移不改变长度，各拐角圆弧的转角之和为 2π。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Point {
    long long x, y;
    bool operator==(const Point &o) const { return x == o.x && y == o.y; }
};
__int128 cross(Point a, Point b, Point c) {
    return (__int128)(b.x - a.x) * (c.y - a.y) - (__int128)(b.y - a.y) * (c.x - a.x);
}
vector<Point> hull(vector<Point> a, bool keep = false) {
    sort(a.begin(), a.end(), [](Point a, Point b) { return tie(a.x, a.y) < tie(b.x, b.y); });
    a.erase(unique(a.begin(), a.end()), a.end());
    if (a.size() < 3)
        return a;
    if (keep) {
        bool line = true;
        for (auto p : a)
            if (cross(a[0], a[1], p) != 0)
                line = false;
        if (line)
            return a;
    }
    vector<Point> h;
    for (auto p : a) {
        while (h.size() >= 2 && (keep ? cross(h[h.size() - 2], h.back(), p) < 0
                                      : cross(h[h.size() - 2], h.back(), p) <= 0))
            h.pop_back();
        h.push_back(p);
    }
    int lower = h.size();
    for (int i = (int)a.size() - 2; i >= 0; i--) {
        auto p = a[i];
        while ((int)h.size() > lower && (keep ? cross(h[h.size() - 2], h.back(), p) < 0
                                              : cross(h[h.size() - 2], h.back(), p) <= 0))
            h.pop_back();
        h.push_back(p);
    }
    h.pop_back();
    return h;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    for (int test = 0; test < tests; test++) {
        int n;
        long long radius;
        cin >> n >> radius;
        vector<Point> a(n);
        for (auto &p : a)
            cin >> p.x >> p.y;
        auto h = hull(a);
        long double perimeter = 2 * acosl(-1.0L) * radius;
        for (int i = 0; i < (int)h.size(); i++) {
            auto a = h[i], b = h[(i + 1) % h.size()];
            perimeter += hypotl(a.x - b.x, a.y - b.y);
        }
        if (test)
            cout << '\n';
        cout << llround(perimeter) << '\n';
    }

    return 0;
}
```

### 实现提醒

不能直接使用凹多边形原周长；圆弧加一整圈；输出整数并保留组间空行。
