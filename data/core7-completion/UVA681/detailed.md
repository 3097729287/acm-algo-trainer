## UVA681 Convex Hull Finding

原题：[UVA681](https://www.luogu.com.cn/problem/UVA681)

### 从问题到算法

原轮廓可能凹陷，但最小凸围栏只保留凸包顶点。按坐标排序后分别扫描下壳与上壳，利用叉积弹掉非凸和共线中间点，得到逆时针边界。

本题起点选择与普通按 x 排序的凸包不同：必须取 y 最小、并列 x 最小者，所以在凸包上再找这个点并旋转列表。旋转不改变顺序和凸性。

原始每组点数已经包含闭合重复点，构造时去重；输出点数则为真正顶点数加一，并再次打印首点。首行输出总组数，组间使用 −1 分隔。详见 [UVA 原始格式](https://onlinejudge.org/external/6/681.pdf)。

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
    cout << tests << '\n';
    for (int test = 0; test < tests; test++) {
        int n;
        cin >> n;
        vector<Point> a(n);
        for (auto &p : a)
            cin >> p.x >> p.y;
        auto h = hull(a);
        int start = min_element(h.begin(), h.end(),
                                [](Point a, Point b) { return tie(a.y, a.x) < tie(b.y, b.x); }) -
                    h.begin();
        rotate(h.begin(), h.begin() + start, h.end());
        cout << h.size() + 1 << '\n';
        for (int i = 0; i <= (int)h.size(); i++)
            cout << h[i % h.size()].x << ' ' << h[i % h.size()].y << '\n';
        if (test + 1 < tests) {
            int delimiter;
            cin >> delimiter;
            cout << -1 << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

最低 y 优先；点数含闭合重复点；仅组间有 -1。
