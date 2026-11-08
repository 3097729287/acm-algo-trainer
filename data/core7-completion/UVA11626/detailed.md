## UVA11626 Convex Hull

原题：[UVA11626](https://www.luogu.com.cn/problem/UVA11626)

### 从问题到算法

输入已给出点是否属于凸包边界的标记，N 点无需保留；Y 点即使位于一条边中间，也必须全部输出。

普通严格凸包会在叉积为零时弹出中间点，本题应把这个条件改为仅在叉积为负时弹出。这样同一条边上的点按行进方向依次出现。上下壳连接时去掉重复端点，起点自然是 x 最小、并列 y 最小者。

如果全部 Y 点共线，通用上下壳会把中间点重复打印，故单独检测并直接输出排序后的点。其它情况，每个边界点恰好出现在一侧凸壳中。

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
    while (tests--) {
        int n;
        cin >> n;
        vector<Point> a;
        for (int i = 0; i < n; i++) {
            Point p;
            char c;
            cin >> p.x >> p.y >> c;
            if (c == 'Y')
                a.push_back(p);
        }
        auto h = hull(a, true);
        cout << h.size() << '\n';
        for (auto p : h)
            cout << p.x << ' ' << p.y << '\n';
    }

    return 0;
}
```

### 实现提醒

保留共线边界点；先过滤 N；全共线时只输出一次。
