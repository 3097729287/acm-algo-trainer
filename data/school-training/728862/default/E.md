## E. T-primes

### 题意

给定最多 $10^5$ 个正整数，每个不超过 $10^{12}$，逐个判断是否恰有三个不同正因数。

### 从零讲：浮点平方根与整数校正

**平方根与类型转换。** `std::sqrtl` 接收、返回 `long double`；`static_cast<long long>(value);` 只做向零截断，不保证得到精确整数平方根，须再做整数校正。`std::vector<bool>` 是布尔标记的压缩容器，单点读写可作常数时间使用；它的元素是代理对象，不应当作普通 `bool` 引用。筛表建好后，本题只查询标记。

### 思路

恰有三个正因数的数，当且仅当它是质数的平方。若 $x=p^2$ 且 $p$ 为质数，因数只有 $1,p,p^2$；反之，中间那个唯一因数必须与自己配对，因此 $x$ 是平方数，平方根也不能是合数。

由于 $x\le10^{12}$，只需筛出 $10^6$ 以内的质数。求整数平方根 $r$，检查 $r^2=x$ 且 $r$ 是质数。开平方后用整数乘法校正，避免边界误差。总时间 $O(10^6\log\log10^6+n)$，空间 $O(10^6)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
using ll = long long;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int M = 1000000;
    vector<bool> prime(M + 1, true);
    prime[0] = prime[1] = false;
    for (int p = 2; p * p <= M; ++p) {
        if (prime[p]) {
            for (int v = p * p; v <= M; v += p) prime[v] = false;
        }
    }
    int n;
    cin >> n;
    while (n--) {
        ll x;
        cin >> x;
        ll r = static_cast<ll>(sqrtl(static_cast<long double>(x)));
        // 浮点平方根只给候选值，再用整数运算校正。
        while ((r + 1) * (r + 1) <= x) ++r;
        while (r * r > x) --r;
        cout << (r * r == x && prime[r] ? "YES" : "NO") << '\n';
    }
}
```

### 易错点

一不是质数；平方根为合数的平方数也不合格；最终用整数乘法确认完全平方。
