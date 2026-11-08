## P1069 细胞分裂

原题：[P1069](https://www.luogu.com.cn/problem/P1069)

### 思路

分解目标数量 m1^m2。对于每种细胞的单次分裂倍率 s，分解同一批质因子，所需时间是各个目标指数除以 s 中对应指数的向上取整最大值；缺少目标质因子的细胞不可行。

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
