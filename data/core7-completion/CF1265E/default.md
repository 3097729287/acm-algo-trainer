## CF1265E Beautiful Mirrors

原题：[CF1265E](https://www.luogu.com.cn/problem/CF1265E)

### 思路

设 E[i] 为从头通过前 i 面镜子的期望次数。到第 i 面前平均已经花 E[i−1] 次，再尝试一次；失败就整段重来，因此 E[i]=(E[i−1]+1)/p[i]。

### 复杂度

时间 O(n log MOD)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long P = 998244353;
    auto power = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long E = 0;
    for (int i = 0; i < n; i++) {
        long long p;
        cin >> p;
        E = (E + 1) * 100 % P * power(p, P - 2) % P;
    }
    cout << E << '\n';

    return 0;
}
```

### 实现提醒

失败回到第一面；百分数转为 100 的因子；分母非零。
