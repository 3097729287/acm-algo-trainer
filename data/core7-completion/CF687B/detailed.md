## CF687B Remainders Game

原题：[CF687B](https://www.luogu.com.cn/problem/CF687B)

### 从问题到算法

两个整数对所有给定模数取余相同，当且仅当它们之差被所有模数整除，也就是被这些模数的最小公倍数 L 整除。要进一步保证它们模 k 相同，就必须且只须 k 整除 L。

实际 L 可能极大，但只关心 k 所含的质因数及指数。把每个 a_i 替换为 gcd(a_i,k) 后，所有因子都来自 k，不影响判断 k 是否被最终 lcm 覆盖。累积 lcm 永远是 k 的因数，不会爆炸。

更新时写 current/gcd(current,g)*g，先除再乘。读完全部数后，current==k 就输出 Yes，否则 No。

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
