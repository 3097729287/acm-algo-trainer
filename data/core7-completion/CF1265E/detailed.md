## CF1265E Beautiful Mirrors

原题：[CF1265E](https://www.luogu.com.cn/problem/CF1265E)

### 从问题到算法

把“到达并尝试第 i 面”看成一次完整尝试周期，周期成本期望为 E[i−1]+1。成功概率 p[i]，失败后返回开头，恢复为同一个问题，所以 E[i]=E[i−1]+1+(1−p[i])E[i]。移项便得到递推。

题目用百分整数输入概率，p[i]=a[i]/100，在模质数下递推为 (E[i−1]+1)·100·inv(a[i])。概率非零保证逆元存在。

必须先给前段期望加一再整体除以成功率，不能只给当前一次尝试乘逆概率。

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
