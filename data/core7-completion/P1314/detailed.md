## P1314 聪明的质监员

原题：[P1314](https://www.luogu.com.cn/problem/P1314)

### 从问题到算法

固定 W 后，令 count 前缀统计 w≥W 的矿石个数，sum 前缀统计它们的价值和。一个区间的检验值就是两段前缀差的乘积，因此一次评估为 O(n+m)。

W 增大只会移走一些正价值矿石，个数与和都不会增，所以 y(W) 单调不增。若 y>s，就需要增大 W；若 y<s，就需要减小 W。在搜索过程中更新最小绝对差，最后必覆盖跨越 s 的两个相邻阈值；阶梯函数的其它值不可能更接近。

搜索范围包括 maxWeight+1，它使所有区间检验值为零。累加检验值可能远超六十四位，使用 __int128；答案初始 s，因为全空方案已保证差值不超过 s。

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
