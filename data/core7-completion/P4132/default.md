## P4132 算不出的等式

原题：[P4132](https://www.luogu.com.cn/problem/P4132)

### 思路

当 p、q 为不同奇质数时，两段求和分别数出矩形格点在直线两侧的数量，总和为 ((p−1)/2)((q−1)/2)。若两质数相等，直接求两份 1+…+(p−1)/2。

### 复杂度

时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    unsigned long long p, q;
    cin >> p >> q;
    auto a = (p - 1) / 2, b = (q - 1) / 2;
    cout << (p == q ? a * (a + 1) : a * b) << '\n';

    return 0;
}
```

### 实现提醒

不能遗漏 p=q；使用 unsigned long long 保存乘积。
