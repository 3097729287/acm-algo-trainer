## CF14E Camels

原题：[CF14E](https://www.luogu.com.cn/problem/CF14E)

### 从问题到算法

相邻高度不能相等，所以每段只有上升或下降。上升转下降形成峰，下降转上升形成谷。二者交替出现，峰数比谷数多一当且仅当起始趋势上升、结束趋势下降。

因此不用同时记录谷数。状态 dp[peaks][lastHeight][trend]，添加一个不同新高度时决定新趋势；若旧上升、新下降，峰数加一，其余不变。高度只有一到四，转移数是常数。

初始两点枚举所有严格上升高度组合，峰数零。最终累加 t 峰、下降趋势的全部末高度，自动保证恰有 t−1 个谷。计数使用六十四位，全部候选至多 4·3^(n−1)。

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
