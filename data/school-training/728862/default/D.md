## D. Minimum Product

### 题意

每次将 $a$ 或 $b$ 减一，分别不能低于 $x,y$，最多操作 $n$ 次，求最小乘积。各数不超过 $10^9$，最多 $2\times10^4$ 组。

### 从零讲：按值传参与整数类型

**按值传参。** 函数形参 `long long a;` 是实参的一份值副本，在函数中减少它，不会改动调用处变量，因而可以安全尝试两种顺序。`std::min(u,v)` 返回两者较小值，两个参数应使用相容类型。整数溢出发生在运算时，把已经溢出的 `int` 乘积存入 `long long` 无法补救。

### 思路

分别尝试“先尽量减 $a$，剩余次数减 $b$”和“先尽量减 $b$，剩余次数减 $a$”，取两者乘积的较小值。

为何只看这两种？令实际使用的次数为 $s=\min(n,a-x+b-y)$，给 $a$ 的次数为 $d$，则给 $b$ 的次数为 $s-d$，乘积为

$$f(d)=(a-d)(b-s+d)=a(b-s)+(a-b+s)d-d^2.$$

合法的 $d$ 构成一个整数区间，且二次项系数为负。这个开口向下的函数在区间上的最小值必在端点；两个端点恰好对应优先减某一个数。每组 $O(1)$ 时间、$O(1)$ 空间。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
using ll = long long;

ll firstA(ll a, ll b, ll x, ll y, ll n) {
    ll take = min(n, a - x);
    a -= take;
    n -= take;
    b -= min(n, b - y);
    return a * b;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        ll a, b, x, y, n;
        cin >> a >> b >> x >> y >> n;
        // 两个端点：先尽量减 a，或先尽量减 b。
        cout << min(firstA(a, b, x, y, n), firstA(b, a, y, x, n)) << '\n';
    }
}
```

### 易错点

乘法用 `long long`；交换两个数时同时交换下限；次数过多时不能减穿下限。
