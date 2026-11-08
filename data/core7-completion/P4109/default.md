## P4109 定价

原题：[P4109](https://www.luogu.com.cn/problem/P4109)

### 思路

枚举 10 的幂作为末尾零因子。对每种因子，检查区间内最小的倍数，以及去零后末位为 5 的最小倍数，比较真实荒谬度，并列取最小价格。

### 复杂度

每组时间 O(log² R)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        long long l, r;
        cin >> l >> r;
        int best = INT_MAX;
        long long answer = l;
        auto test = [&](long long p) {
            if (p < l || p > r)
                return;
            long long x = p;
            while (x % 10 == 0)
                x /= 10;
            int score = 2 * (int)to_string(x).size() - (x % 10 == 5);
            if (score < best || (score == best && p < answer)) {
                best = score;
                answer = p;
            }
        };
        for (long long power = 1; power <= r; power *= 10) {
            long long q = (l + power - 1) / power;
            test(q * power);
            long long five = q + (5 - q % 10 + 10) % 10;
            test(five * power);
        }
        cout << answer << '\n';
    }

    return 0;
}
```

### 实现提醒

候选必须在 [L,R]；并列取更小；最小倍数使用向上取整。
