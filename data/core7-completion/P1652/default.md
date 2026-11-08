## P1652 圆

原题：[P1652](https://www.luogu.com.cn/problem/P1652)

### 思路

对每个圆，若起终点一个在内部、一个在外部，则任何连续曲线都必须穿过它的边界一次；两点在同一侧时可以避开。统计内外状态不同的圆数。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> x(n), y(n), r(n);
    for (auto &v : x)
        cin >> v;
    for (auto &v : y)
        cin >> v;
    for (auto &v : r)
        cin >> v;
    long long x1, y1, x2, y2;
    cin >> x1 >> y1 >> x2 >> y2;
    int ans = 0;
    for (int i = 0; i < n; i++) {
        bool a = (x1 - x[i]) * (x1 - x[i]) + (y1 - y[i]) * (y1 - y[i]) < r[i] * r[i];
        bool b = (x2 - x[i]) * (x2 - x[i]) + (y2 - y[i]) * (y2 - y[i]) < r[i] * r[i];
        ans += a != b;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

圆参数按三组数组读取；用平方比较；起终点保证不在圆周上。
