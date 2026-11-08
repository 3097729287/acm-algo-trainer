## P2957 Barn Echoes G

原题：[P2957](https://www.luogu.com.cn/problem/P2957)

### 思路

重合可以是第一串后缀与第二串前缀，也可以反过来。枚举长度并比较两种方向，取最大的相等长度。

### 复杂度

时间 O(L²)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string a, b;
    cin >> a >> b;
    int ans = 0;
    for (int len = 1; len <= (int)min(a.size(), b.size()); len++)
        if (a.compare(a.size() - len, len, b, 0, len) == 0 ||
            b.compare(b.size() - len, len, a, 0, len) == 0)
            ans = len;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

两个方向都检查；允许整个较短串成为重合部分。
