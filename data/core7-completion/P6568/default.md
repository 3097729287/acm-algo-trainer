## P6568 水壶

原题：[P6568](https://www.luogu.com.cn/problem/P6568)

### 思路

要把连续 s 个水壶的水集中到最右侧，至少且只需 s−1 次倾倒。最多 k 次操作能汇集最多 k+1 个连续水壶，非负水量下取长度恰为 k+1 的最大窗口和。

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
