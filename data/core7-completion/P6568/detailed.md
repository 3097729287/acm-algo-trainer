## P6568 水壶

原题：[P6568](https://www.luogu.com.cn/problem/P6568)

### 从问题到算法

水只能向右流。最终选中某个水壶时，能流入的初始水壶一定来自它左侧的一个连续区间；要跨过区间中每条边，至少执行一次对应倾倒。区间长度 s 需要至少 s−1 次。

从左到右把水逐次倒向下一壶，恰好 s−1 次即可汇集整个区间，所以这个下界可达。由于 A 非负，较短区间可以扩充到 k+1 长度而不变差，问题变为定长最大区间和。

先算首个窗口，每次向右移动时减去离开的数、加上新数，维护最大值。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    long long sum = accumulate(a.begin(), a.begin() + k + 1, 0LL), ans = sum;
    for (int r = k + 1; r < n; r++) {
        sum += a[r] - a[r - k - 1];
        ans = max(ans, sum);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

操作次数比壶数少一；只能向右汇集；k=0 时取最大单项。
