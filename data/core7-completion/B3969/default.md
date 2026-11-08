## B3969 B-smooth 数

原题：[B3969](https://www.luogu.com.cn/problem/B3969)

### 思路

筛出 n 以内的质数，将所有大于 B 的质数的倍数标为不合法。剩下的正整数恰好没有过大的质因子，统计即可。

### 复杂度

时间 O(n log log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, B;
    cin >> n >> B;
    vector<bool> composite(n + 1), bad(n + 1);
    for (int p = 2; p <= n; p++)
        if (!composite[p]) {
            if (1LL * p * p <= n)
                for (int j = p * p; j <= n; j += p)
                    composite[j] = 1;
            if (p > B)
                for (int j = p; j <= n; j += p)
                    bad[j] = 1;
        }
    int ans = 0;
    for (int i = 1; i <= n; i++)
        ans += !bad[i];
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

一也算；不能只判断数本身是否大于 B；标记所有倍数。
