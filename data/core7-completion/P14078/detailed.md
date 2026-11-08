## P14078 金币收集

原题：[P14078](https://www.luogu.com.cn/problem/P14078)

### 从问题到算法

从 (x1,t1) 到 (x2,t2) 只能右移或等待，条件是 x2≥x1 且 t2−t1≥x2−x1，第二个条件等价于 t2−x2≥t1−x1。因此变换后变成两维非降链。

从零出发要求 x≥0、t−x≥0。满足这两个条件的点按 x、t−x 升序排序，第一维已经合法，剩下求第二维最长不下降子序列。用 upper_bound 替换牌堆顶，允许相等值延长。

同一位置同一时刻出现多枚金币可以同时收走，它们对应完全相同的点，应分别计数，不能去重。

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
    cin >> n;
    vector<pair<long long, long long>> points;
    for (int i = 0; i < n; i++) {
        long long x, t;
        cin >> x >> t;
        if (x >= 0 && t >= x)
            points.push_back({x, t - x});
    }
    sort(points.begin(), points.end());
    vector<long long> tails;
    for (auto [x, y] : points) {
        auto it = upper_bound(tails.begin(), tails.end(), y);
        if (it == tails.end())
            tails.push_back(y);
        else
            *it = y;
    }
    cout << tails.size() << '\n';

    return 0;
}
```

### 实现提醒

第二维是 t−x；用 upper_bound 允许相等；同点金币不能去重。
