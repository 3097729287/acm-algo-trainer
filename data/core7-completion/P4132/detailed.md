## P4132 算不出的等式

原题：[P4132](https://www.luogu.com.cn/problem/P4132)

### 从问题到算法

在横坐标 1 到 (p−1)/2、纵坐标 1 到 (q−1)/2 的整数格点矩形中，固定横坐标 k，floor(kq/p) 数出直线 y=qx/p 下方的格点；交换两轴后，另一段求和数出直线上方的格点。

若 p、q 是不同质数，它们互质，矩形内部没有落在直线上的整数格点，因为 px=qy 会要求 p 整除 x，而 x<p。于是两部分不重不漏地覆盖整个矩形，答案就是长乘宽。

原题只说两个奇质数，没有要求不同。p=q 时，两份 floor(kq/p) 都等于 k，答案为 h(h+1)，其中 h=(p−1)/2。这个分支不能误用无对角格点的公式。

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
