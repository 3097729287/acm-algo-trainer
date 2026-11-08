## P1854 花店橱窗布置

原题：[P1854](https://www.luogu.com.cn/problem/P1854)

### 思路

dp[i][j] 表示前 i 束花放进前 j 个花瓶的最大价值。第 j 瓶可以空着，也可以放第 i 束花。记录取舍后从 dp[F][V] 回溯方案。

### 复杂度

时间 O(FV)，空间 O(FV)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int F, V;
    cin >> F >> V;
    vector<vector<int>> a(F + 1, vector<int>(V + 1));
    for (int i = 1; i <= F; i++)
        for (int j = 1; j <= V; j++)
            cin >> a[i][j];
    const int NEG = -1000000000;
    vector<vector<int>> dp(F + 1, vector<int>(V + 1, NEG));
    vector<vector<char>> take(F + 1, vector<char>(V + 1));
    for (int j = 0; j <= V; j++)
        dp[0][j] = 0;
    for (int i = 1; i <= F; i++)
        for (int j = 1; j <= V; j++) {
            dp[i][j] = dp[i][j - 1];
            if (dp[i - 1][j - 1] != NEG && dp[i - 1][j - 1] + a[i][j] > dp[i][j]) {
                dp[i][j] = dp[i - 1][j - 1] + a[i][j];
                take[i][j] = 1;
            }
        }
    cout << dp[F][V] << '\n';
    vector<int> path;
    for (int i = F, j = V; i;) {
        if (take[i][j]) {
            path.push_back(j);
            i--;
        }
        j--;
    }
    reverse(path.begin(), path.end());
    for (int i = 0; i < F; i++)
        cout << path[i] << (i + 1 == F ? '\n' : ' ');

    return 0;
}
```

### 实现提醒

必须放完所有花；价值可能为负；输出方案也需核对最优值。
