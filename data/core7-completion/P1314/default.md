## P1314 聪明的质监员

原题：[P1314](https://www.luogu.com.cn/problem/P1314)

### 思路

阈值 W 增大时，每个区间的合格数量与价值和都不增，检验值单调不增。每次用两组前缀和计算检验值，二分跨过 s 的位置，并保留搜索中最小差值。

### 复杂度

时间 O((n+m) log max w)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    long long target;
    cin >> n >> m >> target;
    vector<int> w(n + 1), v(n + 1);
    int maximum = 0;
    for (int i = 1; i <= n; i++) {
        cin >> w[i] >> v[i];
        maximum = max(maximum, w[i]);
    }
    vector<pair<int, int>> ranges(m);
    for (auto &[l, r] : ranges)
        cin >> l >> r;
    vector<long long> cnt(n + 1), sum(n + 1);
    auto value = [&](int W) {
        for (int i = 1; i <= n; i++) {
            bool take = w[i] >= W;
            cnt[i] = cnt[i - 1] + take;
            sum[i] = sum[i - 1] + (take ? v[i] : 0);
        }
        __int128 y = 0;
        for (auto [l, r] : ranges)
            y += (__int128)(cnt[r] - cnt[l - 1]) * (sum[r] - sum[l - 1]);
        return y;
    };
    long long ans = target;
    int lo = 0, hi = maximum + 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        __int128 y = value(mid), diff = y - target;
        if (diff < 0)
            diff = -diff;
        if (diff < ans)
            ans = diff;
        if (y > target)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

比较的是总检验值；区间可以重复；中间乘积和总和用 __int128。
