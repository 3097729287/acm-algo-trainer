## P2924 Largest Fence G

原题：[P2924](https://www.luogu.com.cn/problem/P2924)

### 从问题到算法

任何凸多边形都有唯一的字典序最小顶点，枚举它作为起点后，其它顶点都在右半平面，可以按相对起点的极角依次访问。凸性只需检查连续三点严格左转；首尾与起点处的转向由极角次序自动保证。

令 dp[i][j] 表示从起点出发，以 i、j 为最后两点的最长凸链顶点数。要接上 k，要求 cross(j−i,k−j)>0，等价于从 j 看，前驱 i 的方向位于后继 k 方向逆时针旋转零到一百八十度之间。起点作为特殊前驱时，当前链有两个顶点。

固定中间点 j，把所有前驱方向按角度排序并复制一圈，再将后继查询也按方向排序。每个查询需要在一个长度为半圈的开区间中取最大链长。随着查询角度递增，区间两端单调移动，用单调队列维护最大值，每个前驱只加入、删除常数次。

由此每个起点的每个中点处理 O(n log n)，总计 O(n³ log n)，而非直接四重枚举。原题保证无三点共线，所以半圆端点没有需要猜测的共线取舍。每次成功扩展都形成一条更长凸链，同时更新全局答案。

### 复杂度

时间 O(n³ log n)，空间 O(n²)。

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

    int n;
    cin >> n;
    vector<Point> points(n);
    for (auto &p : points)
        cin >> p.x >> p.y;
    sort(points.begin(), points.end(),
         [](Point a, Point b) { return tie(a.x, a.y) < tie(b.x, b.y); });
    const long double pi = acosl(-1.0L);
    auto angle = [&](Point a, Point b) {
        long double v = atan2l(b.y - a.y, b.x - a.x);
        if (v < 0)
            v += 2 * pi;
        return v;
    };
    int answer = min(n, 2);
    for (int start = 0; start + 2 < n; start++) {
        Point root = points[start];
        vector<Point> a(points.begin() + start + 1, points.end());
        sort(a.begin(), a.end(), [&](Point x, Point y) { return cross(root, x, y) > 0; });
        int count = a.size();
        vector<vector<int>> dp(count, vector<int>(count));
        for (int middle = 0; middle + 1 < count; middle++) {
            vector<pair<long double, int>> previous = {{angle(a[middle], root), 2}};
            for (int i = 0; i < middle; i++)
                if (dp[i][middle])
                    previous.push_back({angle(a[middle], a[i]), dp[i][middle]});
            sort(previous.begin(), previous.end());
            int size = previous.size();
            for (int i = 0; i < size; i++)
                previous.push_back({previous[i].first + 2 * pi, previous[i].second});
            vector<pair<long double, int>> queries;
            for (int k = middle + 1; k < count; k++)
                queries.push_back({angle(a[middle], a[k]), k});
            sort(queries.begin(), queries.end());
            deque<int> queue;
            int l = 0, r = 0;
            for (auto [theta, k] : queries) {
                while (r < (int)previous.size() && previous[r].first < theta + pi) {
                    while (!queue.empty() && previous[queue.back()].second <= previous[r].second)
                        queue.pop_back();
                    queue.push_back(r++);
                }
                while (l < r && previous[l].first <= theta)
                    l++;
                while (!queue.empty() && queue.front() < l)
                    queue.pop_front();
                if (!queue.empty()) {
                    dp[middle][k] = previous[queue.front()].second + 1;
                    answer = max(answer, dp[middle][k]);
                }
            }
        }
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

按最左最低点枚举且只取其后点；转向必须严格为正；角度区间复制一圈处理跨零。
