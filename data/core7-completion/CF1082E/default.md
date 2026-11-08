## CF1082E Increasing Frequency

原题：[CF1082E](https://www.luogu.com.cn/problem/CF1082E)

### 思路

选择把某个值 x 变成 c 后，区间收益为 x 的个数减 c 的个数。每遇到一个 x，扣去与上次 x 之间的 c 数量，再决定延续旧段或从当前重新开始。

### 复杂度

期望时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, c;
    cin >> n >> c;
    unordered_map<int, pair<int, int>> state;
    state.reserve(2 * n + 1);
    int countC = 0, gain = 0;
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        if (x == c) {
            countC++;
            continue;
        }
        auto &[best, last] = state[x];
        best = max(1, best - (countC - last) + 1);
        last = countC;
        gain = max(gain, best);
    }
    cout << countC + gain << '\n';

    return 0;
}
```

### 实现提醒

区间内原 c 会减少；不同 x 的状态独立；从当前 x 重新开始的收益为一。
