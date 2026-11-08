## P2036 PERKET

原题：[P2036](https://www.luogu.com.cn/problem/P2036)

### 思路

每种配料选或不选，枚举所有非空子集。酸度连乘、苦度相加，比较二者差的绝对值，取最小。

### 复杂度

时间 O(n·2^n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> s(n), b(n);
    for (int i = 0; i < n; i++)
        cin >> s[i] >> b[i];
    long long ans = LLONG_MAX;
    for (int mask = 1; mask < (1 << n); mask++) {
        long long sour = 1, bitter = 0;
        for (int i = 0; i < n; i++)
            if ((mask >> i) & 1) {
                sour *= s[i];
                bitter += b[i];
            }
        ans = min(ans, llabs(sour - bitter));
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

不枚举空集；酸度乘积初始为 1，苦度和初始为 0。
