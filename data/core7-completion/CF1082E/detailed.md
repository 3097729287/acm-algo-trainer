## CF1082E Increasing Frequency

原题：[CF1082E](https://www.luogu.com.cn/problem/CF1082E)

### 从问题到算法

一次加法只能把一种原值 x 变成 c，同时区间中的原 c 会被移走。因此净增加量就是区间内 #x−#c，其它值不影响收益。固定 x 后相当于 +1、−1、零序列的最大子段和。

不能为每个 x 单独扫描全数组。维护全局已见 c 数 C，以及每种 x 的 bestEnding 和上次遇到它时的 C。下次遇到 x 时，间隔里 c 的惩罚为 C−lastC[x]，更新 bestEnding=max(1,bestEnding−惩罚+1)。间隔中的其它值为零，不需处理。

最大净收益加上原数组全部 c 数就是答案。若保持原状最优，可以选择加零，收益下界为零。

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
