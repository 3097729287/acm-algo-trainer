## P5451 密码学第三次小作业

原题：[P5451](https://www.luogu.com.cn/problem/P5451)

### 从问题到算法

题目保证 e1、e2 互质，存在整数 a、b 使 ae1+be2=1。密文代入后，c1^a c2^b≡m^(ae1+be2)≡m，因此不需要分解模数，也不需要求私钥。

a、b 中可能有负数。由于 m 与 N 互质，两份密文也与 N 互质，所以负指数可以改为逆元的正指数。再用扩展欧几里得求密文模 N 的逆元，并规范化到非负余数。

N 接近有符号六十四位上限，两个模内数相乘会超出 long long，模乘必须先转 __int128。扩展欧几里得的系数运算同样使用 __int128，避免中间减乘溢出。

### 复杂度

每组时间 O(log N+log e1+log e2)，空间 O(log N) 递归栈。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long egcd(long long a, long long b, __int128 &x, __int128 &y) {
    if (!b) {
        x = 1;
        y = 0;
        return a;
    }
    __int128 u, v;
    long long g = egcd(b, a % b, u, v);
    x = v;
    y = u - (__int128)(a / b) * v;
    return g;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long c1, c2, e1, e2, N;
        cin >> c1 >> c2 >> e1 >> e2 >> N;
        __int128 a, b;
        egcd(e1, e2, a, b);
        auto inverse = [&](long long x) {
            __int128 u, v;
            egcd(x, N, u, v);
            u %= N;
            if (u < 0)
                u += N;
            return (long long)u;
        };
        auto power = [&](long long x, __int128 exponent) {
            if (exponent < 0) {
                x = inverse(x);
                exponent = -exponent;
            }
            long long r = 1;
            for (; exponent; exponent >>= 1, x = (__int128)x * x % N)
                if (exponent & 1)
                    r = (__int128)r * x % N;
            return r;
        };
        cout << (long long)((__int128)power(c1, a) * power(c2, b) % N) << '\n';
    }

    return 0;
}
```

### 实现提醒

负指数先求逆；所有余数规范化；不能用普通 long long 乘法直接取模。
