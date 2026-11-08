## P4058 木材

原题：[P4058](https://www.luogu.com.cn/problem/P4058)

### 从问题到算法

随时间增加，每棵树只会长高，已达到最低高度要求的树不会重新失去资格，可获得的总木材量因此单调不减。

判定某月时，对每棵树计算当前高度；小于 L 的不计，否则加入总量。达到 S 就可提前返回，避免累加无关大数。高度乘法和总量使用 __int128，以覆盖月份和生长速度的乘积。

先从零月检查，若不够则把右界从一不断翻倍，直到找到可行时间，再在零到右界之间找第一个可行值。这样无需猜测紧的答案上界。

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
