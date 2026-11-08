## P10026 哀之变化

原题：[P10026](https://www.luogu.com.cn/problem/P10026)

### 从问题到算法

一次减一之后若还有 j 次翻倍，它对最终值的减少量就是 2^j。因此固定翻倍次数 d 后，剩下 s=k−d 次减一，要把 D=2^d−n 表示成恰好 s 个二次幂。

非负整数 D 的最少二次幂项数为 popcount(D)，最多为 D；把一个大于一的幂拆成两个较小幂，会让项数恰增加一，所以这两个界之间的所有项数都能实现。

对 n>0 且 2^d>=n，D 的 d 位二进制恰为 n−1 的按位补，故 popcount(D)=d−popcount(n−1)。条件变为 d<=k、2d<=k+popcount(n−1)，以及 k−d<=2^d−n。前两者给出 d 上界，最后一式随着 d 增大只会更容易满足，因此取最大允许 d 即可判断。

d>=61 时，2^d 已大于 n+k 的最大可能和，可直接判为满足而不真的移位。n=0 时先从一减到零，之后任意次翻倍仍为零，所以恰好任意正次数都可行。

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
