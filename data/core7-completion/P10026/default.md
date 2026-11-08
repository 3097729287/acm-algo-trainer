## P10026 哀之变化

原题：[P10026](https://www.luogu.com.cn/problem/P10026)

### 思路

若做 d 次翻倍，最终 n=2^d−D，D 是 k−d 个二次幂之和。对 n>0，D 的最少项数为 d−popcount(n−1)，最多为 D；选满足最少项数限制的最大 d，再判断最多项数是否足够。

### 复杂度

每组时间 O(1)，空间 O(1)。

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
        unsigned long long k, n;
        cin >> k >> n;
        bool ok;
        if (n == 0)
            ok = k >= 1;
        else {
            unsigned long long ones = __builtin_popcountll(n - 1), d = min(k, (k + ones) / 2);
            if (d >= 61)
                ok = true;
            else {
                unsigned long long value = 1ULL << d;
                ok = value >= n && value - n >= k - d;
            }
        }
        cout << (ok ? "Yes" : "No") << '\n';
    }

    return 0;
}
```

### 实现提醒

次数必须恰好；n=0 另处理；大指数先判断，不能执行超范围移位。
