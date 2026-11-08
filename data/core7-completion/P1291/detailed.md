## P1291 百事世界杯之旅

原题：[P1291](https://www.luogu.com.cn/problem/P1291)

### 从问题到算法

把收集过程分成从 k 种到 k+1 种的 n 个阶段。每瓶独立等概率出现一个名字，尚未拥有的名字有 n−k 种，所以成功概率为 (n−k)/n。几何分布的等待期望为概率的倒数。

由期望线性性，总期望为 Σ(k=0..n−1)n/(n−k)=nH_n。逐项用最大公约数通分、加分子并约分，避免小数损失。n<=33 时这些约分后的整数能用 long long 保存。

最后把分子除以分母得到整数部分和余数。余数为零就只输出整数；否则分子和分母前补与整数部分位数相同的空格，中间分数线长度等于分母位数。

### 复杂度

时间 O(n log 分母)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    long long numerator = 0, denominator = 1;
    for (long long i = 1; i <= n; i++) {
        long long g = gcd(denominator, i);
        numerator = numerator * (i / g) + n * (denominator / g);
        denominator *= i / g;
        g = gcd(numerator, denominator);
        numerator /= g;
        denominator /= g;
    }
    long long whole = numerator / denominator, rem = numerator % denominator;
    if (!rem)
        cout << whole << '\n';
    else {
        string pad(to_string(whole).size(), ' ');
        cout << pad << rem << '\n'
             << whole << string(to_string(denominator).size(), '-') << '\n'
             << pad << denominator << '\n';
    }

    return 0;
}
```

### 实现提醒

用精确分数；每次约分；分数线与上下两行起点对齐。
