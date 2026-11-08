## P9035 Pont des souvenirs

原题：[P9035](https://www.luogu.com.cn/problem/P9035)

### 从问题到算法

序列不降，只要最大的两个数之和≤k+1，其它任意两数也满足。若最大值≤h，限制自动成立，从 h 种值中可重复选 n 个，共 C(n+h−1,n)。

若最大值 x>h，不能出现两次，其余 n−1 个数都≤k+1−x=y。它们有 C(n+y−2,n−1) 种选择。x 从 h+1 到 k，等价于 y 从一到 k−h，求和由组合恒等式变为 C(n+k−h−1,n)。

两类互斥且覆盖所有序列。n=1 同一公式仍给出 h+(k−h)=k；组合数上标小于下标时定义为零。先读全部询问，按实际最大上标预处理阶乘和逆阶乘。

### 复杂度

设最大组合数上标为 V，预处理 O(V)，每组 O(1)，空间 O(V+T)。

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
    int V = 0;
    for (auto &[n, k] : queries) {
        cin >> n >> k;
        int h = (k + 1) / 2;
        V = max({V, n + h - 1, n + k - h - 1});
    }
    vector<int> f(V + 1, 1), inv(V + 1, 1);
    for (int i = 1; i <= V; i++)
        f[i] = 1LL * f[i - 1] * i % MOD;
    inv[V] = power(f[V], MOD - 2);
    for (int i = V; i >= 1; i--)
        inv[i - 1] = 1LL * inv[i] * i % MOD;
    auto C = [&](int n, int k) -> long long {
        if (n < k || k < 0)
            return 0;
        return 1LL * f[n] * inv[k] % MOD * inv[n - k] % MOD;
    };
    for (auto [n, k] : queries) {
        int h = (k + 1) / 2;
        cout << (C(n + h - 1, n) + C(n + k - h - 1, n)) % MOD << '\n';
    }

    return 0;
}
```

### 实现提醒

最大值大于一半时只能一次；组合数越界返回零；单元素也适用。
