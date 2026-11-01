## E. T-primes

### 题意

给定最多 $10^5$ 个正整数，每个不超过 $10^{12}$，逐个判断是否恰有三个不同正因数。

### 从零讲：浮点平方根与整数校正

**平方根与类型转换。** `std::sqrtl` 接收、返回 `long double`；`static_cast<long long>(value);` 只做向零截断，不保证得到精确整数平方根，须再做整数校正。`std::vector<bool>` 是布尔标记的压缩容器，单点读写可作常数时间使用；它的元素是代理对象，不应当作普通 `bool` 引用。筛表建好后，本题只查询标记。

### 思路

先区分平方数和质数平方：$4$ 的因数为 $1,2,4$，符合要求；$16$ 的因数为 $1,2,4,8,16$，虽然也是平方数，却不符合要求。

为什么判据没有遗漏？正因数总能按 $d$ 与 $x/d$ 配对。恰有三个因数时，$1$ 与 $x$ 配成一对，剩余的一个因数 $r$ 只能与自己配对，所以 $x=r^2$。如果 $r$ 不是质数，存在 $1<q<r$ 且 $q\mid r$，那么 $q$ 也是 $x$ 的额外因数，与“只有三个”矛盾。因此 $r$ 必为质数。反方向直接列出 $1,r,r^2$ 即可。

多达 $10^5$ 次询问，不应对每个 $x$ 都试除到 $\sqrt{x}$。所有可能的平方根最多为 $10^6$，一次埃氏筛就能准备好答案。开始把 $2$ 及以上都看作可能的质数；扫描到仍被标记为质数的 $p$ 时，划掉 $p^2,p^2+p,\ldots$。比 $p^2$ 小的 $p$ 的合数倍已经有更小的质因数，会被此前筛掉。

`std::sqrtl` 计算浮点平方根，转换为整数后得到候选 $r$。随后用两个循环确保 $r^2\le x<(r+1)^2$，再判相等。这里乘积不超过 $10^{12}$ 的量级，`long long` 足够。特别地，$1$ 不是质数平方，筛表必须把 $0,1$ 标为非质数。

筛表时间 $O(M\log\log M)$、空间 $O(M)$，其中 $M=10^6$；每个询问在本题固定整数范围内花常数时间。

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
