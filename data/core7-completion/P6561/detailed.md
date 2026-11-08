## P6561 人

原题：[P6561](https://www.luogu.com.cn/problem/P6561)

### 从问题到算法

把相邻的一奇一偶位置分成 m 对。选出的奇数不能与它右侧和左侧的偶数相邻，限制只发生在相邻对之间。

可以按奇数选择形成的连续段计数，再为偶数在未被封锁的位置中选点，用两次 Vandermonde 卷积整理，得到 C(m−b,a)C(m−a,b)。这个式子也可解释为删除所选偶数占用的 b 个间隙后选 a 个奇位、对称地删除 a 个间隙后选 b 个偶位，两组压缩坐标唯一还原原来的不相邻排列。

例如 m=4,a=2,b=1，结果为 C(3,2)C(2,1)=6，与样例六个集合一致。约束 a+b<=m 保证组合数下标合法。全部询问共用到最大 m 的阶乘与逆阶乘，模数为 998244353。

### 复杂度

预处理 O(max m)，每组 O(1)，空间 O(max m+T)。

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

    int tests;
    cin >> tests;
    vector<array<int, 3>> queries(tests);
    int limit = 0;
    for (auto &q : queries) {
        cin >> q[0] >> q[1] >> q[2];
        limit = max(limit, q[0]);
    }
    const long long mod = 998244353;
    vector<long long> fact(limit + 1, 1), inv(limit + 1, 1);
    for (int i = 1; i <= limit; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[limit] = power(fact[limit], mod - 2, mod);
    for (int i = limit; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int n, int k) {
        if (k < 0 || k > n)
            return 0LL;
        return fact[n] * inv[k] % mod * inv[n - k] % mod;
    };
    for (auto q : queries) {
        auto [m, a, b] = q;
        cout << choose(m - b, a) * choose(m - a, b) % mod << '\n';
    }

    return 0;
}
```

### 实现提醒

a、b 区分奇偶；组合数是 m−b 选 a 与 m−a 选 b；乘法及时取模。
