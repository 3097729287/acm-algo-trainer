## P1025 数的划分

原题：[P1025](https://www.luogu.com.cn/problem/P1025)

### 从问题到算法

划分不区分各部分的先后，所以同一组正整数若按任意顺序枚举，会重复。规定每一份不小于前一份后，每个划分就有唯一表示。

状态 solve(sum,count,minimum) 表示还需 count 个不小于 minimum 的正整数凑成 sum。下一份 x 不能大于 sum/count，否则剩余每份都至少 x，总和就会超过 sum。枚举 minimum 到 sum/count，递归求 sum−x、count−1、x。

只剩一份时，只要 sum>=minimum 就恰有一种分法。该终止条件同时处理相等部分，不需要集合去重。

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
