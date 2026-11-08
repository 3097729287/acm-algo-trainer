## P1990 覆盖墙壁

原题：[P1990](https://www.luogu.com.cn/problem/P1990)

### 从问题到算法

除完整的二乘 n 墙外，还需考虑末端缺一格的两种对称状态，因为 L 形砖会留下这种边界。完整状态可以接一块竖砖、两块横砖，或从缺角状态补一块 L 形砖；缺角状态可继续横向延伸，或从更短的完整状态产生。

把左右对称的缺角状态合在一起，得到 f[n]=f[n−1]+f[n−2]+2g[n−1]，g[n]=g[n−1]+f[n−2]。将相邻两式相减消去 g，即 f[n]=2f[n−1]+f[n−3]。

空墙有一种覆盖，宽一和宽二分别有一、两种。每步对一万取模，得到后四位数值，按题目输出整数，不补固定四位前导零。

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
