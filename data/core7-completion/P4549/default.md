## P4549 裴蜀定理

原题：[P4549](https://www.luogu.com.cn/problem/P4549)

### 思路

裴蜀定理说明，整数系数线性组合能得到的最小正整数就是所有输入数绝对值的最大公约数。逐项求 gcd 即可。

### 复杂度

时间 O(n log A)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long g = 0;
    while (n--) {
        long long x;
        cin >> x;
        g = gcd(g, llabs(x));
    }
    cout << g << '\n';

    return 0;
}
```

### 实现提醒

系数可为负数；输入取绝对值；累积 gcd 从 0 开始。
