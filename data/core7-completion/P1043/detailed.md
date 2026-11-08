## P1043 数字游戏

原题：[P1043](https://www.luogu.com.cn/problem/P1043)

### 从问题到算法

任意环形划分都可以从某个分组边界切开变成线性划分；枚举全部 n 个起点就不会漏掉最优方案。复制数组并做前缀和，任意一组的值可常数时间计算。

令 low[g][i]、high[g][i] 为前 i 个数恰分 g 个非空组的最小、最大乘积。枚举前 g−1 组结束位置 j，最后一组值 v 是区间和对十的非负余数，再分别更新 low[g−1][j]·v 与 high[g−1][j]·v。

v 始终非负，所以乘积最小值只需前态最小值、最大值只需最大值。初始零组零元素乘积为一，不可能状态单独标记。最终在所有起点的结果中取最小与最大。

### 复杂度

时间 O(mn³)，空间 O(mn)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> pre(2 * n + 1), a(n);
    for (auto &x : a)
        cin >> x;
    for (int i = 1; i <= 2 * n; i++)
        pre[i] = pre[i - 1] + a[(i - 1) % n];
    long long answerMin = LLONG_MAX, answerMax = 0;
    for (int start = 0; start < n; start++) {
        const long long INF = LLONG_MAX / 4;
        vector<vector<long long>> lo(m + 1, vector<long long>(n + 1, INF)),
            hi(m + 1, vector<long long>(n + 1, -1));
        lo[0][0] = hi[0][0] = 1;
        for (int g = 1; g <= m; g++)
            for (int i = g; i <= n; i++)
                for (int j = g - 1; j < i; j++)
                    if (hi[g - 1][j] >= 0) {
                        long long v = ((pre[start + i] - pre[start + j]) % 10 + 10) % 10;
                        lo[g][i] = min(lo[g][i], lo[g - 1][j] * v);
                        hi[g][i] = max(hi[g][i], hi[g - 1][j] * v);
                    }
        answerMin = min(answerMin, lo[m][n]);
        answerMax = max(answerMax, hi[m][n]);
    }
    cout << answerMin << '\n' << answerMax << '\n';

    return 0;
}
```

### 实现提醒

每组非空；负数取模要加十；零组的空乘积是一。
