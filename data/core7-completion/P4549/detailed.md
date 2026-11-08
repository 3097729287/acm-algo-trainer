## P4549 裴蜀定理

原题：[P4549](https://www.luogu.com.cn/problem/P4549)

### 从问题到算法

两个整数 a、b 的所有整数线性组合 ax+by 都是 gcd(a,b) 的倍数；扩展欧几里得算法又保证 gcd(a,b) 本身能被某组整数系数表示。所以最小正值就是这个 gcd。

对多个数，可以先把前两个数能形成的组合压缩为它们的 gcd，再与第三个数合并，依次进行，最终得到全部数的 gcd。负号不改变公约数，因此统一取绝对值。

累积变量初始化为零，利用 gcd(0,a)=|a| 自然处理第一个数。题目允许零时，它不会影响其余数的 gcd。

### 复杂度

时间 O(n log A)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long g = 0;
    while (n--) {
        long long x;
        cin >> x;
        g = gcd(g, llabs(x));
    }
    cout << g << '\n';

    return 0;
}
```

### 实现提醒

系数可为负数；输入取绝对值；累积 gcd 从 0 开始。
