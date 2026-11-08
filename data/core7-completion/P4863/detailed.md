## P4863 JerryC Loves Driving

原题：[P4863](https://www.luogu.com.cn/problem/P4863)

### 从问题到算法

内层贡献的符号只取决于 j，因此可以把二重循环交换：固定 j，计算它对所有 i<=N 的贡献。前面不足 j 的 i 商为零，不必另外限制 i>=j。

令 q=N/j。商 1 到 q−1 各出现 j 次，最后的 q 出现 N−qj+1 次，所以商之和为 j·q(q−1)/2+q(N−qj+1)。j 为偶数时加入，为奇数时减去。

每个 j 只进行常数次运算，前缀计算从平方降为线性。最后用两个前缀相减得到闭区间 [A,B] 的结果。中间乘积使用 long long，负答案正常保留。

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
