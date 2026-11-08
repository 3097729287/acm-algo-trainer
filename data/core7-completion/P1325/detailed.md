## P1325 雷达安装

原题：[P1325](https://www.luogu.com.cn/problem/P1325)

### 从问题到算法

雷达到岛屿的距离不超过 d，设雷达横坐标 t，由 (t−x)²+y²<=d² 得到一个允许 t 的闭区间。若 |y|>d，根本不存在可覆盖它的 x 轴位置，整题无解。

现在要求最少点，使每个区间都至少包含一个点。把区间按右端从小到大排列。当前最早结束的未覆盖区间必须选一个点，将它放在右端不会比更左的位置覆盖更少的后续区间，因为后续右端都不小于它。

若上一个选点已经位于当前区间内，无需新增；否则在当前右端放点。这个交换论证保证每次选择都能保留某个最优解。注意区间是闭合的，边界相等时已覆盖。

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
