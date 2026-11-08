## P14576 Lamborghini (Remix)

原题：[P14576](https://www.luogu.com.cn/problem/P14576)

### 思路

把所有行连成一条坐标轴，行间跨越也算一步。所有光标同步平移，所以彼此距离不变。目标选最长一行，求有多少个行末坐标能落在长度为最长行长的窗口中。

### 复杂度

每组时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<long long> position(n);
        long long current = 0, width = 0;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            width = max(width, x);
            current += x + 1;
            position[i] = current - 1;
        }
        int l = 0, ans = 0;
        for (int r = 0; r < n; r++) {
            while (position[r] - position[l] > width)
                l++;
            ans = max(ans, r - l + 1);
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

行间换行也占一次移动；窗口比较坐标差，不是位置数；前缀和用 long long。
