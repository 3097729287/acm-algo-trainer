## CF687B Remainders Game

原题：[CF687B](https://www.luogu.com.cn/problem/CF687B)

### 思路

所有给定余数把原数确定到它们最小公倍数的同余类。能确定模 k 的余数，当且仅当 k 整除这个最小公倍数。只累积 gcd(a_i,k) 的 lcm，避免大整数。

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
    long long k;
    cin >> n >> k;
    long long value = 1;
    while (n--) {
        long long x;
        cin >> x;
        long long g = gcd(x, k);
        value = value / gcd(value, g) * g;
    }
    cout << (value == k ? "Yes" : "No") << '\n';

    return 0;
}
```

### 实现提醒

不要直接累乘所有数；只保留 k 的因数；lcm 先除后乘。
