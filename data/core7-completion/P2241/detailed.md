## P2241 统计方形（数据加强版）

原题：[P2241](https://www.luogu.com.cn/problem/P2241)

### 从问题到算法

n 行 m 列小方格有 n+1 条横线、m+1 条竖线，任意各取两条就确定一个矩形，所以全部矩形数是两个组合数的乘积。

正方形还要求横纵跨度相同。固定整数边长 k，它的左上角可在 n−k+1 个行位置与 m−k+1 个列位置选择，二者相乘就是这个尺寸的数量。枚举一到两维较小值，所有尺寸互不重复。

题目分别输出正方形与其它矩形，因此第二项必须用全部矩形减去正方形。乘法全程使用六十四位整数。

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
