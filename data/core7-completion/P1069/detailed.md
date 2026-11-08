## P1069 细胞分裂

原题：[P1069](https://www.luogu.com.cn/problem/P1069)

### 从问题到算法

经过 t 次分裂后，细胞总数为 s^t。能平均装进目标数量的试管，等价于 m1^m2 整除 s^t。

设 m1 中质因子 p 的指数为 e，目标就需要 e·m2 个 p；若 s 中 p 的指数为 c，那么 t 轮提供 c·t 个，要求 t>=ceil(e·m2/c)。所有质因子同时满足，所以对每种细胞取这些下界的最大值。某个所需质因子完全不在 s 中，则无论多久都不行。

在全部可行细胞中选最小时间。m1=1 时目标为一，初始一个细胞已经能满足，时间为零。不必实际计算巨大的幂。

### 复杂度

时间 O(sqrt m1+n·质因子数·log s)，空间 O(质因子数)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m1, m2;
    cin >> n >> m1 >> m2;
    vector<pair<long long, long long>> factors;
    long long x = m1;
    for (long long p = 2; p <= x / p; p++)
        if (x % p == 0) {
            long long e = 0;
            while (x % p == 0) {
                x /= p;
                e++;
            }
            factors.push_back({p, e * m2});
        }
    if (x > 1)
        factors.push_back({x, m2});
    long long answer = LLONG_MAX;
    while (n--) {
        long long s;
        cin >> s;
        long long time = 0;
        bool ok = true;
        for (auto [p, need] : factors) {
            long long c = 0;
            while (s % p == 0) {
                s /= p;
                c++;
            }
            if (c == 0 && need) {
                ok = false;
                break;
            }
            if (need)
                time = max(time, (need + c - 1) / c);
        }
        if (ok)
            answer = min(answer, time);
    }
    cout << (answer == LLONG_MAX ? -1 : answer) << '\n';

    return 0;
}
```

### 实现提醒

目标指数要乘 m2；每个细胞独立计算；没有可行细胞输出 -1。
