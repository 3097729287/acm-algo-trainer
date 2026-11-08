## P2241 统计方形（数据加强版）

原题：[P2241](https://www.luogu.com.cn/problem/P2241)

### 思路

全部矩形由两条横边与两条竖边确定，共 C(n+1,2)C(m+1,2)。边长 k 的正方形有 (n−k+1)(m−k+1) 个，枚举 k 求和，再相减得到非正方形矩形数。

### 复杂度

时间 O(min(n,m))，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, m;
    cin >> n >> m;
    long long squares = 0;
    for (long long k = 1; k <= min(n, m); k++)
        squares += (n - k + 1) * (m - k + 1);
    long long total = n * (n + 1) / 2 * (m * (m + 1) / 2);
    cout << squares << ' ' << total - squares << '\n';

    return 0;
}
```

### 实现提醒

边界线比小格数多一；第二项不包含正方形；乘法使用 long long。
