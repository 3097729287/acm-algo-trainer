## P2424 约数和

原题：[P2424](https://www.luogu.com.cn/problem/P2424)

### 思路

约数 d 在 1 到 N 中出现 floor(N/d) 次，因此前缀约数和为 Σ d·floor(N/d)。同一商对应一段连续的 d，用等差数列求和，区间答案是 F(y)−F(x−1)。

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
