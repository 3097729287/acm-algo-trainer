## P1043 数字游戏

原题：[P1043](https://www.luogu.com.cn/problem/P1043)

### 思路

复制一份环形数组，枚举长度 n 的线性窗口。每个窗口按组数和前缀长度 DP，枚举最后一组起点，以该组和模十后的值相乘，分别维护最小值和最大值。

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
