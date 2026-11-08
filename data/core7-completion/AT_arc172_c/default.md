## AT_arc172_c Election

原题：[AT_arc172_c](https://www.luogu.com.cn/problem/AT_arc172_c)

### 思路

把第一张选票依次向后移动，与相邻选票交换。两种开票顺序只会在交换中间的那一次公布结果上不同。累计真正改变结果的相邻交换次数，再加一。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    auto sign = [](int x) { return (x > 0) - (x < 0); };
    int first = s[0] == 'A' ? 1 : -1, difference = 0, ans = 1;
    for (int i = 1; i < n; i++) {
        int v = s[i] == 'A' ? 1 : -1;
        if (sign(difference + first) != sign(difference + v))
            ans++;
        difference += v;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

统计公布结果的不同序列，不是开票顺序；差值需在比较后再加入当前票。
