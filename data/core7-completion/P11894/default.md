## P11894 Update

原题：[P11894](https://www.luogu.com.cn/problem/P11894)

### 思路

每个位置最终只取决于被覆盖的次数。先用差分求次数，再利用 floor(log2 x) 在相邻二次幂之间恒定，整段跳过若干次相同增量。

### 复杂度

时间 O(n log A+m)，空间 O(n)，A 为操作后的最大值。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    vector<int> difference(n + 2);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    while (m--) {
        int l, r;
        cin >> l >> r;
        difference[l]++;
        difference[r + 1]--;
    }
    int count = 0;
    for (int i = 1; i <= n; i++) {
        count += difference[i];
        long long left = count, x = a[i];
        while (left && x > 1) {
            int b = 63 - __builtin_clzll(x);
            long long gap = (1LL << (b + 1)) - x, steps = min(left, (gap + b - 1) / b);
            x += steps * b;
            left -= steps;
        }
        cout << x << (i == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

x=1 不动；跳跃次数向上取整；更新后的最高位重新计算。
