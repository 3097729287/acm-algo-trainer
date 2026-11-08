## P2742 二维凸包 / [USACO5.1] 圈奶牛Fencing the Cows

原题：[P2742](https://www.luogu.com.cn/problem/P2742)

### 从问题到算法

最短围住全部点的绳子只会接触凸包边界，凹进去的折线可以直接拉直并缩短，所以只需求凸包的周长。

坐标字典序排序后，从左到右维护下壳。若最后两个壳点与新点不构成逆时针转向，当前中间点不可能位于下凸壳上，弹出再判断。反向扫描得到上壳，去掉重复端点并拼接。

叉积为零的中间共线点也可弹出，因为保留直线段两端不影响周长。最后包括末点回到首点的边。距离用 hypot 计算，结果按两位小数输出。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
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
```

### 实现提醒

先排序并去重；周长包含闭合边；共线中间点不影响长度。
