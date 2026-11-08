## UVA116 单向TSP Unidirectional TSP

原题：[UVA116](https://www.luogu.com.cn/problem/UVA116)

### 从问题到算法

从右到左计算，转移到下一列的上一行、本行、下一行，行号首尾循环。先将三个候选行按编号排序，只在费用严格更小时替换选择，这样平价时保留行号最小的候选。

为什么只看下一行即可得到字典序最小路径？当前位置固定，第一处可能不同就是下一行；下一行较小的路径字典序必较小。同一下一行的后缀已由 DP 保证最优且字典序最小。因此局部打破平局可以归纳到整条路径。

起点也从小行号扫描，只在费用严格降低时替换。读到文件结束，每组输出一行从一开始的行号序列，再输出总费用。

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
