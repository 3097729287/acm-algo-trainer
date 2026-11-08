## P1025 数的划分

原题：[P1025](https://www.luogu.com.cn/problem/P1025)

### 思路

把每个划分按非递减顺序写出，只枚举这种规范顺序，避免同一组数的排列重复。递归记录剩余和、剩余份数与下一份最小值。

### 复杂度

时间为实际枚举的划分状态数，递归空间 O(k)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    function<long long(int, int, int)> solve = [&](int sum, int count, int minimum) -> long long {
        if (count == 1)
            return sum >= minimum;
        long long ans = 0;
        for (int x = minimum; x <= sum / count; x++)
            ans += solve(sum - x, count - 1, x);
        return ans;
    };
    cout << solve(n, k, 1) << '\n';

    return 0;
}
```

### 实现提醒

各份必须正数；下一份可以等于上一份；上界用剩余和除剩余份数。
