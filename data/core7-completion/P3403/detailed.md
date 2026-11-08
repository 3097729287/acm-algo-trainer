## P3403 跳楼机

原题：[P3403](https://www.luogu.com.cn/problem/P3403)

### 从问题到算法

任意可达楼层再加 x 仍可达，因此对每个模 x 余数，只需知道最小可达值 dist[r]。从一楼出发，对“加 y”“加 z”建立余数图边，边权就是实际增加的楼层数；加 x 不改变余数且不会改善最小值，可以省略。

用 Dijkstra 求余数图最短路，初始 dist[1%x]=1。若 dist[r]≤h，该余数贡献 floor((h−dist[r])/x)+1。不同余数不重叠，直接求和。

把三种步长排序以减小状态数。h 可能达到有符号六十四位上界，松弛时先判断 dist≤h−step，避免加法溢出；超过楼顶的状态无须访问。

### 复杂度

设 x 为最小步长，时间 O(x log x)，空间 O(x)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long h;
    array<int, 3> a;
    cin >> h >> a[0] >> a[1] >> a[2];
    sort(a.begin(), a.end());
    int x = a[0];
    vector<long long> d(x, -1);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[1 % x] = 1;
    q.push({1, 1 % x});
    while (!q.empty()) {
        auto [v, r] = q.top();
        q.pop();
        if (d[r] != v)
            continue;
        for (int step : {a[1], a[2]})
            if (h >= step && v <= h - step) {
                long long nd = v + step;
                int nr = (r + step) % x;
                if (d[nr] < 0 || nd < d[nr]) {
                    d[nr] = nd;
                    q.push({nd, nr});
                }
            }
    }
    long long ans = 0;
    for (long long v : d)
        if (v >= 0 && v <= h)
            ans += (h - v) / x + 1;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

从一楼开始；不会把零楼算入；大整数加法先检查上界。
