## UVA675 Convex Hull of the Polygon

原题：[UVA675](https://www.luogu.com.cn/problem/UVA675)

### 从问题到算法

单调链先构造上下凸壳：若加入新点使最后一次转向不是逆时针，就删除中间点，直到恢复凸性。叉积为零的中间点也删除，确保输出转角严格小于一百八十度。

凸包构造后的起点通常是坐标最小点，但本题要求使用原输入序列中第一个属于凸包顶点的点。保留原顺序，逐个查找它是否出现在凸包顶点列表，再旋转列表，保持原有逆时针方向。

输入以空行分隔多组，坐标带逗号；每组末尾可能重复起点，排序去重时自然消除。输出再次在末尾重复起点，多组之间留空行。格式按 [UVA 原始题面](https://onlinejudge.org/external/6/675.pdf) 核对。

### 复杂度

时间 O(n log n+n·h)，空间 O(n)，h 为凸包点数。

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

    vector<Point> points;
    bool first = true;
    auto output = [&]() {
        if (points.empty())
            return;
        auto h = hull(points);
        int start = 0;
        for (auto p : points) {
            auto it = find(h.begin(), h.end(), p);
            if (it != h.end()) {
                start = it - h.begin();
                break;
            }
        }
        rotate(h.begin(), h.begin() + start, h.end());
        if (!first)
            cout << '\n';
        first = false;
        for (int i = 0; i <= (int)h.size(); i++) {
            auto p = h[i % h.size()];
            cout << p.x << ", " << p.y << '\n';
        }
        points.clear();
    };
    string line;
    while (getline(cin, line)) {
        if (line.find_first_not_of(" \t\r") == string::npos) {
            output();
            continue;
        }
        for (char &c : line)
            if (c == ',')
                c = ' ';
        stringstream input(line);
        Point p;
        if (input >> p.x >> p.y)
            points.push_back(p);
    }
    output();

    return 0;
}
```

### 实现提醒

按原输入挑起点；逆时针；重复首点闭合；组间空行。
