## UVA11388 GCD LCM

原题：[UVA11388](https://www.luogu.com.cn/problem/UVA11388)

### 思路

若给出的最小公倍数不能被最大公约数整除，就无解。否则直接取这两个数本身，它们的 gcd 与 lcm 恰好符合要求。

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
