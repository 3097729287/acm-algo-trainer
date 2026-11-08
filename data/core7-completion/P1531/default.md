## P1531 I Hate It

原题：[P1531](https://www.luogu.com.cn/problem/P1531)

### 思路

用线段树保存每段的最大成绩。修改沿叶子到根更新最大值，查询把目标区间拆成若干完整节点并取最大值。

### 复杂度

建树 O(n)，每次操作 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        int size = 1;
        while (size < n)
            size *= 2;
        vector<int> t(2 * size, INT_MIN);
        for (int i = 0; i < n; i++)
            cin >> t[size + i];
        for (int i = size - 1; i; i--)
            t[i] = max(t[i * 2], t[i * 2 + 1]);
        while (m--) {
            char op;
            int x, y;
            cin >> op >> x >> y;
            if (op == 'U') {
                int p = size + x - 1;
                t[p] = y;
                for (p /= 2; p; p /= 2)
                    t[p] = max(t[p * 2], t[p * 2 + 1]);
            } else {
                if (x > y)
                    swap(x, y);
                int ans = INT_MIN;
                for (int l = size + x - 1, r = size + y; l < r; l /= 2, r /= 2) {
                    if (l & 1)
                        ans = max(ans, t[l++]);
                    if (r & 1)
                        ans = max(ans, t[--r]);
                }
                cout << ans << '\n';
            }
        }
    }

    return 0;
}
```

### 实现提醒

更新是赋值；输入到 EOF；最大值查询的空段使用最小整数。
