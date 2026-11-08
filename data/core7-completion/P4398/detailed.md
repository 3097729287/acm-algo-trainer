## P4398 Blue Mary的战役地图

原题：[P4398](https://www.luogu.com.cn/problem/P4398)

### 从问题到算法

两个公共子矩阵一旦选定左上角，它们对应格子的横纵坐标差就是固定平移。因此枚举所有从 −n+1 到 n−1 的横纵位移，就覆盖了全部公共子矩阵的对齐方式。

固定平移后，把对应值相等的格子视作一，不等或超出另一图范围的视作零。令 dp[i][j] 为以当前格为右下角的最大全一正方形边长。当前格为零时值为零；为一时，必须同时拥有上方、左方、左上方三个可扩展正方形，所以取三者最小值加一。

这个判定逐格比较原整数，完全避免二维哈希的碰撞。n 至多五十，O(n⁴) 的直接计算可以接受。每个平移都清空 DP，不能让上一种对齐的信息混入。

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
