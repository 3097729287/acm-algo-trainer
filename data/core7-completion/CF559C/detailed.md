## CF559C Gerald and Giant Chess

原题：[CF559C](https://www.luogu.com.cn/problem/CF559C)

### 从问题到算法

没有障碍时，从 (1,1) 到 (x,y) 需要 x−1 次向下和 y−1 次向右，路径数为 C(x+y−2,x−1)。

把障碍坐标排序并将终点放在最后。令 dp[i] 表示到第 i 个特殊点、且没有经过其它较早障碍的路径数。先赋总路径数，再对每个坐标不大于它的此前障碍 j，减去 dp[j]·C(dx+dy,dx)。

被扣掉的路径按首次到达的障碍 j 分组，dp[j] 已保证到它之前没有其它障碍，所以不同 j 的类别互不重复。乘上的组合数负责障碍之后到当前点的任意单调走法。终点的 dp 就是完全避开障碍的答案。

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
