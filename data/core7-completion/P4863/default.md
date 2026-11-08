## P4863 JerryC Loves Driving

原题：[P4863](https://www.luogu.com.cn/problem/P4863)

### 思路

用前缀函数 F(N) 表示 1 到 N 的总愉悦值。交换求和顺序后，对每个 j 计算 Σ(i=1..N) floor(i/j)，再按 j 奇偶加减；区间答案为 F(B)−F(A−1)。

### 复杂度

时间 O(B)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a, b;
    cin >> a >> b;
    auto solve = [](long long n) {
        long long ans = 0;
        for (long long j = 1; j <= n; j++) {
            long long q = n / j;
            long long value = j * q * (q - 1) / 2 + q * (n - q * j + 1);
            ans += (j % 2 ? -value : value);
        }
        return ans;
    };
    cout << solve(b) - solve(a - 1) << '\n';

    return 0;
}
```

### 实现提醒

(-1)^j 对奇数是负；F(0)=0；乘法先用六十四位。
