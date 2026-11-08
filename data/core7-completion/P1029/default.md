## P1029 最大公约数和最小公倍数问题

原题：[P1029](https://www.luogu.com.cn/problem/P1029)

### 思路

设两个数为 x·a、x·b，则需要 a·b=y/x 且 gcd(a,b)=1。枚举 y/x 的因子 a，检查互补因子是否互质；不相同的一对贡献两个有序数对。

### 复杂度

时间 O(sqrt(y/x)·log(y/x))，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y;
    cin >> x >> y;
    if (y % x) {
        cout << 0 << '\n';
        return 0;
    }
    long long p = y / x, ans = 0;
    for (long long a = 1; a <= p / a; a++)
        if (p % a == 0 && gcd(a, p / a) == 1)
            ans += a == p / a ? 1 : 2;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

有序数对需计交换；x 不整除 y 时为零。
