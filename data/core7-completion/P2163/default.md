## P2163 园丁的烦恼

原题：[P2163](https://www.luogu.com.cn/problem/P2163)

### 思路

将闭矩形计数拆为四个左下无穷前缀。按横坐标排序查询事件和树木，扫描时用树状数组维护已加入点的纵坐标数量，按符号累加答案。

### 复杂度

时间 O((n+m) log(n+m))，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Fenwick {
    int n;
    vector<long long> t;
    explicit Fenwick(int n) : n(n), t(n + 1) {}
    void add(int x, long long v) {
        for (; x <= n; x += x & -x)
            t[x] += v;
    }
    long long sum(int x) const {
        long long s = 0;
        for (; x; x -= x & -x)
            s += t[x];
        return s;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<pair<int, int>> points(n);
    vector<int> ys;
    for (auto &[x, y] : points) {
        cin >> x >> y;
        ys.push_back(y);
    }
    sort(points.begin(), points.end());
    sort(ys.begin(), ys.end());
    ys.erase(unique(ys.begin(), ys.end()), ys.end());
    struct E {
        int x, y, id, sign;
    };
    vector<E> events;
    for (int i = 0; i < m; i++) {
        int a, b, c, d;
        cin >> a >> b >> c >> d;
        events.push_back({c, d, i, 1});
        events.push_back({a - 1, d, i, -1});
        events.push_back({c, b - 1, i, -1});
        events.push_back({a - 1, b - 1, i, 1});
    }
    sort(events.begin(), events.end(), [](E a, E b) { return a.x < b.x; });
    Fenwick bit(ys.size());
    vector<long long> ans(m);
    int p = 0;
    for (auto e : events) {
        while (p < n && points[p].first <= e.x) {
            int r = lower_bound(ys.begin(), ys.end(), points[p].second) - ys.begin() + 1;
            bit.add(r, 1);
            p++;
        }
        int r = upper_bound(ys.begin(), ys.end(), e.y) - ys.begin();
        ans[e.id] += e.sign * bit.sum(r);
    }
    for (auto x : ans)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

闭区间使用 a−1、b−1；同横坐标的点先加入；重复点分别计数。
