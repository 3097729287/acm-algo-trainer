## CF559C Gerald and Giant Chess

原题：[CF559C](https://www.luogu.com.cn/problem/CF559C)

### 思路

把障碍和终点按坐标排序。到每个点的总单调路径是组合数，再减去经过此前各障碍的路径；其中以“首次遇到的障碍”分类，避免重复扣除。

### 复杂度

时间 O(H+W+n²)，空间 O(H+W+n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int h, w, n;
    cin >> h >> w >> n;
    vector<pair<int, int>> points(n);
    for (auto &[x, y] : points)
        cin >> x >> y;
    points.push_back({h, w});
    sort(points.begin(), points.end());
    const long long mod = 1000000007;
    int limit = h + w;
    vector<long long> fact(limit + 1, 1), inv(limit + 1, 1);
    for (int i = 1; i <= limit; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[limit] = power(fact[limit], mod - 2, mod);
    for (int i = limit; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int a, int b) { return fact[a] * inv[b] % mod * inv[a - b] % mod; };
    vector<long long> dp(n + 1);
    for (int i = 0; i <= n; i++) {
        auto [x, y] = points[i];
        dp[i] = choose(x + y - 2, x - 1);
        for (int j = 0; j < i; j++)
            if (points[j].first <= x && points[j].second <= y) {
                int dx = x - points[j].first, dy = y - points[j].second;
                dp[i] = (dp[i] - dp[j] * choose(dx + dy, dx) % mod + mod) % mod;
            }
    }
    cout << dp[n] << '\n';

    return 0;
}
```

### 实现提醒

只有坐标可达的障碍才转移；先前 dp 已排除更早障碍；模数为 1000000007。
