## CF14E Camels

原题：[CF14E](https://www.luogu.com.cn/problem/CF14E)

### 思路

峰比谷恰好多一意味着第一段上升、最后一段下降。先枚举上升的前两个高度，随后 DP 记录末高度、趋势和已出现峰数，最后只取下降且有 t 个峰的状态。

### 复杂度

时间 O(nt·4²)，空间 O(t·4)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, t;
    cin >> n >> t;
    long long dp[11][4][2]{};
    for (int a = 0; a < 4; a++)
        for (int b = a + 1; b < 4; b++)
            dp[0][b][1]++;
    for (int len = 2; len < n; len++) {
        long long next[11][4][2]{};
        for (int p = 0; p <= t; p++)
            for (int h = 0; h < 4; h++)
                for (int up = 0; up < 2; up++)
                    for (int v = 0; v < 4; v++)
                        if (v != h) {
                            int newUp = v > h, np = p + (up && !newUp);
                            if (np <= t)
                                next[np][v][newUp] += dp[p][h][up];
                        }
        memcpy(dp, next, sizeof dp);
    }
    long long ans = 0;
    for (int h = 0; h < 4; h++)
        ans += dp[t][h][0];
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

相邻高度不能相等；峰在趋势翻转时计数；必须首升末降。
