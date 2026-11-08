## P1325 雷达安装

原题：[P1325](https://www.luogu.com.cn/problem/P1325)

### 思路

雷达位于 x 轴。能覆盖岛屿 (x,y) 的雷达横坐标区间为 [x−sqrt(d²−y²),x+sqrt(d²−y²)]。按右端排序，若上个雷达不在当前区间内，就在当前右端再放一个。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
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
```

### 实现提醒

先检查 |y|<=d；区间按右端排序；相等端点算覆盖。
