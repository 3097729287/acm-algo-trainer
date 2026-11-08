## UVA11388 GCD LCM

原题：[UVA11388](https://www.luogu.com.cn/problem/UVA11388)

### 从问题到算法

对于任意两个正整数，最大公约数一定整除最小公倍数，因此 L%G!=0 是不可能条件。

这个条件也是充分的：当 G 整除 L 时，选择 a=G、b=L，就有 gcd(a,b)=G、lcm(a,b)=L。并且任何合法 a 都是 G 的倍数，所以 G 已经是第一个数能够取得的最小值。无需分解质因数，也无需逐个寻找其它数对。

每组测试只做一次取余，成功时输出 G L，失败时按原题输出 -1。

### 复杂度

每组时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        long long g, l;
        cin >> g >> l;
        if (l % g)
            cout << -1 << '\n';
        else
            cout << g << ' ' << l << '\n';
    }

    return 0;
}
```

### 实现提醒

输入顺序是 gcd、lcm；不要计算可能溢出的乘积。
