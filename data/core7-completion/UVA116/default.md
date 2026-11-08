## UVA116 单向TSP Unidirectional TSP

原题：[UVA116](https://www.luogu.com.cn/problem/UVA116)

### 思路

dp[r][c] 表示从该格走到最后一列的最小代价。把下一列的三个可选行排序，费用相同时选编号最小者，记录路径；最后选择最小费用且起始行最小的起点。

### 复杂度

每组时间 O(mn)，空间 O(mn)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    while (cin >> m >> n) {
        vector<vector<long long>> a(m, vector<long long>(n)), dp = a;
        vector<vector<int>> next(m, vector<int>(n));
        for (auto &r : a)
            for (auto &x : r)
                cin >> x;
        for (int r = 0; r < m; r++)
            dp[r][n - 1] = a[r][n - 1];
        for (int c = n - 2; c >= 0; c--)
            for (int r = 0; r < m; r++) {
                array<int, 3> rows = {(r + m - 1) % m, r, (r + 1) % m};
                sort(rows.begin(), rows.end());
                int best = rows[0];
                for (int u : rows)
                    if (dp[u][c + 1] < dp[best][c + 1])
                        best = u;
                dp[r][c] = a[r][c] + dp[best][c + 1];
                next[r][c] = best;
            }
        int root = 0;
        for (int r = 1; r < m; r++)
            if (dp[r][0] < dp[root][0])
                root = r;
        int r = root;
        for (int c = 0; c < n; c++) {
            cout << r + 1 << (c + 1 == n ? '\n' : ' ');
            if (c + 1 < n)
                r = next[r][c];
        }
        cout << dp[root][0] << '\n';
    }

    return 0;
}
```

### 实现提醒

行循环取模；负权也能 DP；费用相等按行号而非几何方向选择。
