## UVA11181 条件概率 Probability|Given

原题：[UVA11181](https://www.luogu.com.cn/problem/UVA11181)

### 思路

枚举恰好 R 个人购买的所有集合，累加集合概率得到条件事件概率；同时把概率加入集合内每个人的分子。各分子除以总概率即为条件购买概率。

### 复杂度

时间 O(n·2^n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, r, test = 0;
    while (cin >> n >> r && (n || r)) {
        vector<double> p(n), numerator(n);
        for (auto &x : p)
            cin >> x;
        double denominator = 0;
        for (int mask = 0; mask < (1 << n); mask++)
            if (__builtin_popcount((unsigned)mask) == r) {
                double probability = 1;
                for (int i = 0; i < n; i++)
                    probability *= ((mask >> i) & 1) ? p[i] : 1 - p[i];
                denominator += probability;
                for (int i = 0; i < n; i++)
                    if ((mask >> i) & 1)
                        numerator[i] += probability;
            }
        cout << "Case " << ++test << ":\n";
        for (double x : numerator)
            cout << fixed << setprecision(6) << x / denominator << '\n';
    }

    return 0;
}
```

### 实现提醒

独立概率相乘；未购买者用 1−p；最后按条件总概率归一化。
