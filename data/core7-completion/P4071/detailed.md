## P4071 排列计数

原题：[P4071](https://www.luogu.com.cn/problem/P4071)

### 从问题到算法

恰好 m 个位置保持原值时，这些位置有 C(n,m) 种选法。删除已固定元素后，其余元素不能出现在自己的位置，正是 n−m 个标号的错排。两步选择独立。

错排递推可按元素一的去向 j 分类。若 j 回到一的位置，两者组成二元环，剩下 D[k−2] 种；否则把一接入 j 所在循环，相当于剩下 k−1 个元素错排，有 D[k−1] 种。j 有 k−1 种选择，所以得到递推。初值 D[0]=1、D[1]=0。

预处理阶乘、逆阶乘与错排数，所有查询常数时间。m>n 时直接为零。

### 复杂度

预处理 O(max n)，每问 O(1)，空间 O(max n+T)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    vector<pair<int, int>> queries(T);
    int N = 0;
    for (auto &[n, m] : queries) {
        cin >> n >> m;
        N = max(N, n);
    }
    vector<long long> f(N + 1, 1), inv(N + 1, 1), d(N + 1);
    d[0] = 1;
    for (int i = 1; i <= N; i++)
        f[i] = f[i - 1] * i % MOD;
    for (int i = 2; i <= N; i++)
        d[i] = (i - 1) * (d[i - 1] + d[i - 2]) % MOD;
    inv[N] = power(f[N], MOD - 2);
    for (int i = N; i >= 1; i--)
        inv[i - 1] = inv[i] * i % MOD;
    for (auto [n, m] : queries)
        cout << (m > n ? 0 : f[n] * inv[m] % MOD * inv[n - m] % MOD * d[n - m] % MOD) << '\n';

    return 0;
}
```

### 实现提醒

空错排有一种；一个元素不能错排；m>n 输出零。
