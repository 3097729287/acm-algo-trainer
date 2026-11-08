## B3969 B-smooth 数

原题：[B3969](https://www.luogu.com.cn/problem/B3969)

### 从问题到算法

一个数不满足 B-smooth，当且仅当它有一个大于 B 的质因子。先用埃氏筛判断质数，再枚举所有 p>B 的质数，把 p 的倍数标为不合法。

不合法数一定会被它的过大质因子标记；被标记的数也确实含这个质因子，所以筛法既不遗漏也不误删。注意一没有任何质因子，应当计入。B≥n 时全部一到 n 都合法。

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
