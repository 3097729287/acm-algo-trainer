## P2181 对角线

原题：[P2181](https://www.luogu.com.cn/problem/P2181)

### 从问题到算法

两条在多边形内部相交的对角线，必须拥有四个不同端点；这些端点沿凸多边形边界交错出现，恰好组成一个凸四边形，两条所选线就是它的两条对角线。

反过来，任取四个顶点，得到的凸四边形两条对角线必定相交。按题目对交点位置的约定，这样每组选出的四顶点贡献一个内部交点，所以只需计算组合数 n(n−1)(n−2)(n−3)/24。

中间四个数的乘积可能先溢出六十四位，因此用 __int128 完成乘法和除法，再十进制输出。少于四个顶点时答案为零。

### 复杂度

时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    if (n < 4) {
        cout << 0 << '\n';
        return 0;
    }
    __int128 value = (__int128)n * (n - 1) * (n - 2) * (n - 3) / 24;
    string s;
    do {
        s.push_back('0' + value % 10);
        value /= 10;
    } while (value);
    reverse(s.begin(), s.end());
    cout << s << '\n';

    return 0;
}
```

### 实现提醒

只数内部对角线交点；先用宽整数计算；n<4 输出 0。
