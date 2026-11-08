## P1854 花店橱窗布置

原题：[P1854](https://www.luogu.com.cn/problem/P1854)

### 从问题到算法

由于花束必须保持顺序，第 j 个花瓶若被使用，它只能承接当前最后一束花 i，前 i−1 束必须放在前 j−1 瓶中。因此 dp[i][j]=max(dp[i][j−1],dp[i−1][j−1]+a[i][j])。

初始 dp[0][j]=0，i>j 等不可能状态设为负无穷。所有花都必须放，不能把负价值状态误初始化成零。

记录每次是否使用当前花瓶，回溯时若使用就保存 j 并让 i、j 同时减一，否则只减 j。回溯结果逆序输出，恰好得到递增花瓶下标；相同最大值可以选择任意一个方案。

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
