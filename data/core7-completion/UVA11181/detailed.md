## UVA11181 条件概率 Probability|Given

原题：[UVA11181](https://www.luogu.com.cn/problem/UVA11181)

### 从问题到算法

每个人独立购买，给定一个购买集合 S，其发生概率为购买者的 p 连乘与未购买者的 (1−p) 连乘。只保留大小恰为 R 的集合，正好组成已知条件事件。

这些集合互斥，因此总概率等于各集合概率之和。对于第 i 人，他购买且总共 R 人购买的联合事件，只需累加所有含 i 的合法集合概率。根据条件概率公式，再除以总事件概率即可。

人数较少，可以用二进制掩码枚举所有集合，先按位数筛掉不符合数量的掩码，再计算概率。每组输出 Case 编号和每人的六位小数。原题保证条件事件可用于查询，不应把不可能条件随意解释为某个概率分布。

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
