## P6075 子集选取

原题：[P6075](https://www.luogu.com.cn/problem/P6075)

### 思路

对一个固定元素，只看它在哪些子集中出现。包含关系把出现区域约束为阶梯形，其边界对应 k 次二元选择，共 2^k 种。n 个元素独立，答案为 2^(nk)。

### 复杂度

时间 O(log n+log k)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, k;
    cin >> n >> k;
    const long long mod = 1000000007;
    cout << power(power(2, k, mod), n, mod) << '\n';

    return 0;
}
```

### 实现提醒

空子集允许；元素彼此独立；模数为 1000000007。
