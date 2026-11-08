## P1291 百事世界杯之旅

原题：[P1291](https://www.luogu.com.cn/problem/P1291)

### 思路

已经收集 k 个名字时，下次拿到新名字的概率为 (n−k)/n，等待期望为 n/(n−k)。相加得到 n·(1+1/2+…+1/n)，用有理数精确累加并按题意排版。

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
