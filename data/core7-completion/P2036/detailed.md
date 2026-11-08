## P2036 PERKET

原题：[P2036](https://www.luogu.com.cn/problem/P2036)

### 从问题到算法

配料不要求连续，也没有可安全丢弃某种组合的单调性，数量较少时直接枚举子集最可靠。二进制掩码的第 i 位表示是否选第 i 种配料。

每个非零掩码都对应唯一非空选择，从酸度乘积一、苦度和零开始，逐个累加被选配料，计算绝对差。空掩码不允许，否则会把没有做出任何食物的状态混入答案。

酸度乘法与差值使用 long long，避免中间乘积先溢出 int。

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
