## P1029 最大公约数和最小公倍数问题

原题：[P1029](https://www.luogu.com.cn/problem/P1029)

### 从问题到算法

若最大公约数是 x，两个数都含有公共因子 x。约去它后，剩下的 a、b 必须互质；此时最小公倍数为 xab，因此 ab=y/x。若 y 不能被 x 整除，立即无解。

枚举 a 从 1 到 sqrt(y/x)，只在它整除乘积时检查 b=(y/x)/a。gcd(a,b)=1 时得到合法数对。题目把先后顺序不同算成不同方案，所以 a!=b 时贡献二；a=b 时只贡献一，这只会在乘积为一的情况下通过互质检查。

循环用 a<=product/a 判断边界，避免直接计算 a² 溢出。

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
