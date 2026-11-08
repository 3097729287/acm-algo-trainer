## P14081 炸弹游戏

原题：[P14081](https://www.luogu.com.cn/problem/P14081)

### 思路

能连出 m 条边要求 C(n,2)≥m，给出最小 n。获胜还要求能把最大独立集压到 m−1，最大的可行 n 为 2m−2。若两界交错则 Lose!，否则输出该区间。

### 复杂度

每组时间 O(log m)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        long long m;
        cin >> m;
        long long l = 1, r = 2 * m;
        while (l < r) {
            long long mid = (l + r) / 2;
            if (mid * (mid - 1) / 2 >= m)
                r = mid;
            else
                l = mid + 1;
        }
        long long high = 2 * m - 2;
        if (l > high)
            cout << "Lose!\n";
        else
            cout << l << ' ' << high << '\n';
    }

    return 0;
}
```

### 实现提醒

不允许重边与自环；m=1、2 由边界比较自然判输；容量乘积用六十四位。
