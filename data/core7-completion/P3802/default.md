## P3802 小魔女帕琪

原题：[P3802](https://www.luogu.com.cn/problem/P3802)

### 思路

总晶体数为 S，每个连续七次施法成为七重奏的概率相同，为 7!∏a_i/[S(S−1)…(S−6)]。共有 S−6 个窗口，乘起来就是期望。

### 复杂度

时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a[7], sum = 0;
    for (auto &x : a) {
        cin >> x;
        sum += x;
    }
    long double ans = 0;
    if (sum >= 7) {
        ans = 5040.0L * (sum - 6);
        for (int i = 0; i < 7; i++)
            ans = ans * a[i] / (sum - i);
    }
    cout << fixed << setprecision(3) << ans << '\n';

    return 0;
}
```

### 实现提醒

重叠窗口都计数；不足七个时为零；某属性数量为零时概率自然为零。
