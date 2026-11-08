## P4398 Blue Mary的战役地图

原题：[P4398](https://www.luogu.com.cn/problem/P4398)

### 思路

固定第二张图相对第一张图的平移后，每对对齐格子的相等关系固定。对重叠区域求全为相等格的最大正方形，枚举所有平移取最大值。

### 复杂度

时间 O(n⁴)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> a(n, vector<int>(n)), b = a;
    for (auto &row : a)
        for (int &x : row)
            cin >> x;
    for (auto &row : b)
        for (int &x : row)
            cin >> x;
    int ans = 0;
    for (int dx = 1 - n; dx < n; dx++)
        for (int dy = 1 - n; dy < n; dy++) {
            vector<vector<int>> dp(n + 1, vector<int>(n + 1));
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++) {
                    int x = i + dx, y = j + dy;
                    if (x >= 0 && x < n && y >= 0 && y < n && a[i][j] == b[x][y]) {
                        dp[i + 1][j + 1] = 1 + min({dp[i][j + 1], dp[i + 1][j], dp[i][j]});
                        ans = max(ans, dp[i + 1][j + 1]);
                    }
                }
        }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

只允许平移，不旋转；越界格当不相等；DP 取三个方向最小值。
