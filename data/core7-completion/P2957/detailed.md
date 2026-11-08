## P2957 Barn Echoes G

原题：[P2957](https://www.luogu.com.cn/problem/P2957)

### 从问题到算法

题目中的重合不要求出现在两个串内部的任意位置，而是必须同时是某串的后缀和另一串的前缀。只有两种方向，都要检查。

对长度 len，从 1 到两个长度的较小值，分别比较 a 的最后 len 个字符与 b 的前 len 个字符，以及 b 的最后 len 个字符与 a 的前 len 个字符。任意一组相等，就能更新答案为 len。

字符串至多八十个字符，直接调用 compare 逐字符比较已经足够，避免为很小的输入引入不必要的哈希与碰撞问题。完全没有非空重合时答案保持零。

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
