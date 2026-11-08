## P1990 覆盖墙壁

原题：[P1990](https://www.luogu.com.cn/problem/P1990)

### 思路

完整覆盖数满足 f[n]=2f[n−1]+f[n−3]，初值 f[0]=f[1]=1、f[2]=2。由完整状态与两种对称缺角状态转移并消元得到，按模 10000 递推。

### 复杂度

时间 O(n)，空间 O(n)，也可滚动到 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> f(max(n + 1, 3));
    f[0] = f[1] = 1;
    f[2] = 2;
    for (int i = 3; i <= n; i++)
        f[i] = (2 * f[i - 1] + f[i - 3]) % 10000;
    cout << f[n] << '\n';

    return 0;
}
```

### 实现提醒

初值包含空墙；模数 10000；横竖砖与 L 形缺角不能漏。
