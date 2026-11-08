## P2181 对角线

原题：[P2181](https://www.luogu.com.cn/problem/P2181)

### 思路

凸多边形中任取四个顶点，其两条对角线在内部相交；每个交点又由唯一一组四顶点确定，因此答案是 C(n,4)。

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
