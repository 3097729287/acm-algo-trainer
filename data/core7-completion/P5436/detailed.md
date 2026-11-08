## P5436 缘分

原题：[P5436](https://www.luogu.com.cn/problem/P5436)

### 从问题到算法

若选的两个整数相等，最小公倍数就是它们本身，不超过 n。若不同，把较大者记为 a、较小者记为 b，则 a<=n、b<=n−1，且 lcm(a,b)<=ab<=n(n−1)。

相邻整数的任何公因数都必须整除它们的差 1，所以 gcd(n,n−1)=1。取这一对时，最小公倍数正好等于乘积，达到了刚才的上界。

唯一特例 n=1，只有 (1,1) 可选，答案为 1。n 可达十亿，乘积要用 long long 保存。

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
        long long n;
        cin >> n;
        cout << (n == 1 ? 1 : n * (n - 1)) << '\n';
    }

    return 0;
}
```

### 实现提醒

n=1 单独处理；乘法用六十四位。
