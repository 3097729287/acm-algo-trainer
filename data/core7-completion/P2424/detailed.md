## P2424 约数和

原题：[P2424](https://www.luogu.com.cn/problem/P2424)

### 从问题到算法

直接对每个整数枚举约数会重复大量工作。反过来固定约数 d：在 1 到 N 中，它整除 d、2d、…，共 floor(N/d) 个数，所以贡献 d·floor(N/d)。

设当前左端为 l，商 q=N/l。这个商保持不变的最远右端为 r=N/q；区间 [l,r] 内的贡献就是 q·(l+r)(r−l+1)/2。结算后令 l=r+1。不同整商只有 O(sqrt N) 种。

定义 F(0)=0，闭区间 [x,y] 的答案为 F(y)−F(x−1)。中间乘积使用 __int128，最终同样用十进制输出，避免先乘后除时溢出。

### 复杂度

时间 O(sqrt y)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y;
    cin >> x >> y;
    auto solve = [](long long n) {
        __int128 ans = 0;
        for (long long l = 1, r; l <= n; l = r + 1) {
            long long q = n / l;
            r = n / q;
            ans += (__int128)(l + r) * (r - l + 1) / 2 * q;
        }
        return ans;
    };
    __int128 v = solve(y) - solve(x - 1);
    string s;
    do {
        s.push_back('0' + v % 10);
        v /= 10;
    } while (v);
    reverse(s.begin(), s.end());
    cout << s << '\n';

    return 0;
}
```

### 实现提醒

右端是 N/(N/l)；x=1 时前缀为 0；乘积先转宽整数。
