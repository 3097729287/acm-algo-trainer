## D. Minimum Product

### 题意

每次将 $a$ 或 $b$ 减一，分别不能低于 $x,y$，最多操作 $n$ 次，求最小乘积。各数不超过 $10^9$，最多 $2\times10^4$ 组。

### 从零讲：按值传参与整数类型

**按值传参。** 函数形参 `long long a;` 是实参的一份值副本，在函数中减少它，不会改动调用处变量，因而可以安全尝试两种顺序。`std::min(u,v)` 返回两者较小值，两个参数应使用相容类型。整数溢出发生在运算时，把已经溢出的 `int` 乘积存入 `long long` 无法补救。

### 思路

不要只根据初始大小决定先减谁。样例 $a=12,b=8,x=8,y=7,n=2$：先减 $a$ 得到 $10\times8=80$；先把 $b$ 减到下限，再减 $a$，得到 $11\times7=77$。

先明确为什么可以尽量用完次数：两个数始终为正，只要还能把其中一个减一，乘积就会下降。因此实际使用次数为 $s=\min(n,(a-x)+(b-y))$；如果次数过多，多余的操作直接不用。

把其中 $d$ 次用于 $a$，另外 $s-d$ 次用于 $b$。限制分别为 $0\le d\le a-x$、$0\le s-d\le b-y$，合起来得到

$$\max(0,s-(b-y))\le d\le\min(s,a-x).$$

在这个区间里，最终乘积为

$$f(d)=(a-d)(b-s+d)=a(b-s)+(a-b+s)d-d^2.$$

负的平方项意味着曲线开口向下：区间内的函数值至少等于两个端点值的较小者，因此只检查左右端点即可。这也适用于整数区间，因为两端点本身就是整数。右端点让 $a$ 尽量多减，左端点让 $b$ 尽量多减。

函数 `firstA` 先算可用于第一个数的次数 `std::min(n, a-x)`，扣除后把剩余次数用于第二个数。交换实参时必须连同两个下限一起交换。所有运算用 `long long`，因为初始乘积能达到 $10^{18}$。每组 $O(1)$ 时间、$O(1)$ 空间。

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
