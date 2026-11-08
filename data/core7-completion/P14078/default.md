## P14078 金币收集

原题：[P14078](https://www.luogu.com.cn/problem/P14078)

### 思路

把金币变为点 (x,t−x)。从一枚走到下一枚，等价于两个坐标都不减。排除起点不可达金币，按第一维、第二维升序排序，再求第二维最长不下降子序列。

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
