## P4058 木材

原题：[P4058](https://www.luogu.com.cn/problem/P4058)

### 思路

给定月份 t，第 i 棵树高为 h_i+a_i·t，只有达到 L 的树才可砍伐。累计可砍高度是否达到 S 是单调条件，二分最早满足的月份。

### 复杂度

时间 O(n log 答案)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long need, limit;
    cin >> n >> need >> limit;
    vector<long long> h(n), growth(n);
    for (auto &x : h)
        cin >> x;
    for (auto &x : growth)
        cin >> x;
    auto ok = [&](long long day) {
        __int128 sum = 0;
        for (int i = 0; i < n; i++) {
            __int128 height = h[i] + (__int128)growth[i] * day;
            if (height >= limit)
                sum += height;
            if (sum >= need)
                return true;
        }
        return false;
    };
    long long l = 0, r = 1;
    while (!ok(r))
        r *= 2;
    while (l < r) {
        long long mid = l + (r - l) / 2;
        if (ok(mid))
            r = mid;
        else
            l = mid + 1;
    }
    cout << l << '\n';

    return 0;
}
```

### 实现提醒

达标后计整棵树高度；零月也可能满足；乘法先转 __int128。
