## P5736 质数筛

原题：[P5736](https://www.luogu.com.cn/problem/P5736)

### 思路

小于二的数不是质数。对每个输入整数检查是否存在 2 到平方根之间的因子，没有就按原顺序输出。

### 复杂度

时间 O(n sqrt A)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    bool first = true;
    while (n--) {
        long long x;
        cin >> x;
        bool prime = x >= 2;
        for (long long d = 2; prime && d <= x / d; d++)
            if (x % d == 0)
                prime = false;
        if (prime) {
            if (!first)
                cout << ' ';
            first = false;
            cout << x;
        }
    }
    cout << '\n';

    return 0;
}
```

### 实现提醒

1 不是质数；保留顺序与重复；平方根条件避免乘法溢出。
