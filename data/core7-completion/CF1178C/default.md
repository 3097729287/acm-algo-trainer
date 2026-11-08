## CF1178C Tiles

原题：[CF1178C](https://www.luogu.com.cn/problem/CF1178C)

### 思路

合法铺法由第一行与第一列的二元选择决定，共有 h+w 个独立二元自由度，因此答案是 2^(h+w)，对 998244353 取模。

### 复杂度

时间 O(log(h+w))，空间 O(1)。

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

    long long h, w;
    cin >> h >> w;
    cout << power(2, h + w, 998244353) << '\n';

    return 0;
}
```

### 实现提醒

指数是 h+w；模数为 998244353。
